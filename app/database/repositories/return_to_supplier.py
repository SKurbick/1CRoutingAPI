from typing import List, Tuple

import asyncpg
from asyncpg import Pool

from app.models.return_to_supplier import ReturnToSupplierUpdate, ReturnToSupplierResponse


class ReturnToSupplierRepository:
    def __init__(self, pool: Pool):
        self.pool = pool

    async def update_data(self, data: List[ReturnToSupplierUpdate]) -> ReturnToSupplierResponse:
        get_products = """SELECT id FROM products;"""
        data_to_update_return_to_supplier: List[Tuple] = []
        data_to_update_return_to_supplier_items: List[Tuple] = []
        guid_data: List[str] = []

        async with self.pool.acquire() as conn:
            products_data = await conn.fetch(get_products)
            ids = [record['id'] for record in products_data]

        for document_data in data:
            guid = document_data.guid
            supply_guid = document_data.supply_guid
            document_number = document_data.document_number
            document_created_at = document_data.document_created_at
            return_date = document_data.return_date
            event_status = document_data.event_status
            our_organizations_name = document_data.our_organizations_name
            update_document_datetime = document_data.update_document_datetime
            author_of_the_change = document_data.author_of_the_change
            supplier_name = document_data.supplier_name
            supplier_code = document_data.supplier_code
            currency = document_data.currency
            guid_data.append(guid)

            for supply_data in document_data.supply_data:
                local_vendor_code = supply_data.local_vendor_code.strip()
                product_name = supply_data.product_name
                quantity = supply_data.quantity
                amount_with_vat = supply_data.amount_with_vat
                amount_without_vat = supply_data.amount_without_vat

                data_to_update_return_to_supplier.append((
                    guid, document_number, document_created_at, return_date,
                    local_vendor_code, product_name, event_status, quantity,
                    amount_with_vat, amount_without_vat, supplier_name, supplier_code,
                    supply_guid, update_document_datetime, author_of_the_change,
                    our_organizations_name, currency,
                ))

                if local_vendor_code in ids and supplier_code != '9714053621':
                    data_to_update_return_to_supplier_items.append((
                        guid, local_vendor_code, quantity, return_date, document_created_at,
                    ))

        update_is_valid_in_return_to_supplier = """
            UPDATE return_to_supplier
            SET is_valid = FALSE
            WHERE guid = ANY($1::varchar[])
              AND is_valid = TRUE
        """
        query_to_insert_return_to_supplier = """
            INSERT INTO return_to_supplier (
                guid, document_number, document_created_at, return_date,
                local_vendor_code, product_name, event_status, quantity,
                amount_with_vat, amount_without_vat, supplier_name, supplier_code,
                supply_guid, update_document_datetime, author_of_the_change,
                our_organizations_name, currency, is_valid
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, True)
        """

        update_is_valid_in_return_to_supplier_items = """
            UPDATE return_to_supplier_items
            SET is_valid = FALSE,
                correction_comment = 'Перезапись документа ' || NOW()
            WHERE guid = ANY($1::varchar[])
              AND is_valid = TRUE
        """
        query_to_insert_return_to_supplier_items = """
            INSERT INTO return_to_supplier_items (guid, product_id, quantity, is_valid, return_date, document_created_at)
            VALUES ($1, $2, $3, True, $4, $5)
        """

        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    await conn.execute(update_is_valid_in_return_to_supplier, guid_data)
                    await conn.executemany(query_to_insert_return_to_supplier, data_to_update_return_to_supplier)

                async with conn.transaction():
                    await conn.execute(update_is_valid_in_return_to_supplier_items, guid_data)
                    await conn.executemany(query_to_insert_return_to_supplier_items, data_to_update_return_to_supplier_items)

            result = ReturnToSupplierResponse(status=201, message="Успешно")
        except asyncpg.PostgresError as e:
            result = ReturnToSupplierResponse(status=422, message="PostgresError", details=str(e))

        return result
