from pprint import pprint
from typing import List, Tuple

import asyncpg
from asyncpg import Pool
from app.models import ReceiptOfGoodsUpdate, AddIncomingReceiptUpdate
from app.models.receipt_of_goods import ReceiptOfGoodsResponse, OneCModelUpdate, SupplyData


class ReceiptOfGoodsRepository:
    def __init__(self, pool: Pool):
        self.pool = pool


    async def get_one_c_model_data(self, guid_data) -> List[OneCModelUpdate]:
        query = """
            SELECT 
                ogfb.guid,
                ogfb.local_vendor_code,
                ogfb.product_name,
                gac.sum_real_quantity as quantity,
                ogfb.amount_with_vat,
                ogfb.amount_without_vat
            FROM ordered_goods_from_buyers AS ogfb
            JOIN goods_acceptance_certificate AS gac ON gac.ordered_goods_from_buyers_id = ogfb.id
            WHERE ogfb.guid = ANY($1::text[]) 
                AND ogfb.is_valid = TRUE 
                AND ogfb.in_acceptance = TRUE 
                AND ogfb.is_printed_barcode = TRUE
        """
        try:
            records = await self.pool.fetch(query, guid_data)

            result = []
            for record in records:
                # Создаем SupplyData
                supply_data = SupplyData(
                    local_vendor_code=record['local_vendor_code'],
                    product_name=record['product_name'],
                    quantity=record['quantity'],
                    amount_with_vat=record['amount_with_vat'],
                    amount_without_vat=record['amount_without_vat']
                )

                # Создаем OneCModelUpdate
                one_c_model = OneCModelUpdate(
                    guid=record['guid'],
                    supply_data=[supply_data]  # список с одним элементом
                )

                result.append(one_c_model)

            return result

        except Exception as e:
            print(f"Error fetching data: {e}")
            return []
        finally:
            await self.pool.close()

    async def update_data(self, data: List[ReceiptOfGoodsUpdate]):
        get_wilds_in_products = """SELECT id FROM products;"""
        data_to_update_incoming_items: List[Tuple] = []
        data_to_update_incoming_documents: List[Tuple] = []
        data_to_update_supply_to_sellers_warehouse: List[Tuple] = []
        guid_data: List[str] = []

        async with self.pool.acquire() as conn:
            products_data = await conn.fetch(get_wilds_in_products)
            ids = [record['id'] for record in products_data]  # получаем все валидные id товаров

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
                product_name = supply_data.product_name
                data_to_update_supply_to_sellers_warehouse.append((guid, document_number, document_created_at, update_document_datetime, event_status,
                                                                   author_of_the_change, our_organizations_name, supply_date, local_vendor_code,
                                                                   quantity, amount_with_vat, amount_without_vat, supplier_name, supplier_code, product_name))

                if local_vendor_code in ids:  # собираем данные для актуализации остатков на складе
                    data_to_update_incoming_items.append(
                        (guid, local_vendor_code, quantity, amount_with_vat)
                    )
                    data_to_update_incoming_documents.append(
                        (guid, document_number, document_created_at, supplier_code)
                    )
        pprint(data_to_update_supply_to_sellers_warehouse)
        update_is_valid_in_supply_to_sellers_warehouse = """
        UPDATE supply_to_sellers_warehouse
        SET is_valid = False
        WHERE guid = ANY($1::varchar[])
        AND is_valid = True
        """
        query_to_insert_supply_to_sellers_warehouse = """
        INSERT INTO supply_to_sellers_warehouse (guid, document_number, document_created_at, update_document_datetime, event_status,
                               author_of_the_change, our_organizations_name, supply_date, local_vendor_code,
                               quantity, amount_with_vat, amount_without_vat, supplier_name, supplier_code, product_name, is_valid)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11,  $12, $13, $14, $15, True); """

        update_is_valid_in_incoming_items = """
        UPDATE incoming_items
        SET is_valid = False
        WHERE guid = ANY($1::varchar[])
        AND is_valid = True
        """
        query_to_insert_incoming_items = """
                INSERT INTO incoming_items (guid, product_id, quantity, price, is_valid)
        VALUES ($1, $2, $3, $4, True) ; """
        query_to_insert_incoming_documents = """
                INSERT INTO incoming_documents (guid, doc_number, doc_date, supplier_code)
        VALUES ($1, $2, $3, $4) 
        ON CONFLICT (guid) DO NOTHING; """

        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    await conn.execute(update_is_valid_in_supply_to_sellers_warehouse, guid_data)
                    await conn.executemany(query_to_insert_supply_to_sellers_warehouse, data_to_update_supply_to_sellers_warehouse)
                #
                async with conn.transaction():  # актуализация поставок для расчета остатков
                    #
                    await conn.execute(update_is_valid_in_incoming_items, guid_data)  # по совпадению guid устанавливаем false
                    await conn.executemany(query_to_insert_incoming_documents, data_to_update_incoming_documents)
                    await conn.executemany(query_to_insert_incoming_items, data_to_update_incoming_items)
                    print("incoming_items data ---->")
                    print(guid_data)
                    print(data_to_update_incoming_documents)
                    print(data_to_update_incoming_items)
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

    async def add_incoming_receipt(self, data: List[AddIncomingReceiptUpdate]):
        get_wilds_in_products = """SELECT id FROM products;"""
        data_to_update_incoming_items: List[Tuple] = []
        data_to_update_incoming_documents: List[Tuple] = []
        guid_data: List[str] = []
        ordered_goods_from_buyers_ids: List[int] = []
        async with self.pool.acquire() as conn:
            products_data = await conn.fetch(get_wilds_in_products)
            ids = [record['id'] for record in products_data]  # получаем все валидные id товаров

        for document_data in data:
            guid = document_data.guid
            document_number = document_data.document_number
            document_created_at = document_data.document_created_at
            supplier_code = document_data.supplier_code
            ordered_goods_from_buyers_id = document_data.ordered_goods_from_buyers_id
            guid_data.append(guid)
            ordered_goods_from_buyers_ids.append(ordered_goods_from_buyers_id)
            for supply_data in document_data.supply_data:
                local_vendor_code = supply_data.local_vendor_code
                quantity = supply_data.quantity
                amount_with_vat = supply_data.amount_with_vat

                if local_vendor_code in ids:  # собираем данные для актуализации остатков на складе
                    data_to_update_incoming_items.append(
                        (guid, local_vendor_code, quantity, amount_with_vat)
                    )
                    data_to_update_incoming_documents.append(
                        (guid, document_number, document_created_at, supplier_code)
                    )

        update_is_valid_in_incoming_items = """
        UPDATE incoming_items
        SET is_valid = False
        WHERE guid = ANY($1::varchar[])
        AND is_valid = True
        """

        query_to_insert_incoming_items = """
                INSERT INTO incoming_items (guid, product_id, quantity, price, is_valid, correction_comment)
        VALUES ($1, $2, $3, $4, True, 'локальное оприходование (данные поступили не через 1С)') ; """
        query_to_insert_incoming_documents = """
                INSERT INTO incoming_documents (guid, doc_number, doc_date, supplier_code)
        VALUES ($1, $2, $3, $4) 
        ON CONFLICT (guid) DO NOTHING; """

        query_update_acceptance_completed = """
            UPDATE ordered_goods_from_buyers
            SET acceptance_completed = True
            WHERE id = ANY($1::integer[]);
        """
        try:
            async with self.pool.acquire() as conn:

                async with conn.transaction():  # актуализация поставок для расчета остатков
                    await conn.execute(update_is_valid_in_incoming_items, guid_data)  # по совпадению guid устанавливаем false
                    await conn.executemany(query_to_insert_incoming_documents, data_to_update_incoming_documents)
                    await conn.executemany(query_to_insert_incoming_items, data_to_update_incoming_items)
                    await conn.execute(query_update_acceptance_completed, ordered_goods_from_buyers_ids)
                    print("incoming_items data ---->")
                    print(guid_data)
                    print(data_to_update_incoming_documents)
                    print(data_to_update_incoming_items)
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
