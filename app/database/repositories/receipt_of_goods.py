from pprint import pprint
from typing import List, Tuple

import asyncpg
from asyncpg import Pool, UniqueViolationError
from app.models import ReceiptOfGoodsUpdate
from app.models.receipt_of_goods import ReceiptOfGoodsResponse


class ReceiptOfGoodsRepository:
    def __init__(self, pool: Pool):
        self.pool = pool

    async def update_data(self, data: List[ReceiptOfGoodsUpdate]):
        data_to_update: List[Tuple] = []
        guid_data: List[str] = []
        for document_data in data:
            guid = document_data.guid
            document_number = document_data.document_number
            document_created_at = document_data.document_created_at
            update_document_datetime = document_data.update_document_datetime
            event_status = document_data.event_status
            author_of_the_change = document_data.author_of_the_change
            our_organizations_name = document_data.our_organizations_name
            supply_date = document_data.supply_date
            supplier_name = document_data.supplier_name
            supplier_code = document_data.supplier_code
            guid_data.append(guid)
            for supply_data in document_data.supply_data:
                local_vendor_code = supply_data.local_vendor_code
                quantity = supply_data.quantity
                amount_with_vat = supply_data.amount_with_vat
                amount_without_vat = supply_data.amount_without_vat

                data_to_update.append((guid, document_number, document_created_at, update_document_datetime, event_status,
                                       author_of_the_change, our_organizations_name, supply_date, local_vendor_code,
                                       quantity, amount_with_vat, amount_without_vat, supplier_name, supplier_code))
        pprint(data_to_update)
        query_to_update = """
        UPDATE supply_to_sellers_warehouse
        SET is_valid = False
        WHERE guid = ANY($1::varchar[])
        AND is_valid = True
        """
        query_to_insert = """
        INSERT INTO supply_to_sellers_warehouse (guid, document_number, document_created_at, update_document_datetime, event_status,
                               author_of_the_change, our_organizations_name, supply_date, local_vendor_code,
                               quantity, amount_with_vat, amount_without_vat, supplier_name, supplier_code, is_valid)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11,  $12, $13, $14, True)
        ;
        """
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    await conn.execute(query_to_update, guid_data)
                    await conn.executemany(query_to_insert, data_to_update)

                result = ReceiptOfGoodsResponse(
                    status=201,
                    message="Успешно")
        except asyncpg.PostgresError as e:
            result = ReceiptOfGoodsResponse(
                status=422,
                message="PostgresError",
                details=str(e)
            )
        return result
