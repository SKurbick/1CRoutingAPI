import datetime
from pprint import pprint
from typing import List, Tuple

import asyncpg
from asyncpg import Pool
from app.models import OrderedGoodsFromBuyersUpdate, OrderedGoodsFromBuyersResponse, OrderedGoodsFromBuyersData
from app.models.ordered_goods_from_buyers import IsAcceptanceStatus


class OrderedGoodsFromBuyersRepository:
    def __init__(self, pool: Pool):
        self.pool = pool

    async def update_data(self, data: List[OrderedGoodsFromBuyersUpdate]):
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
                product_name = supply_data.product_name
                data_to_update.append((guid, document_number, document_created_at, update_document_datetime, event_status,
                                       author_of_the_change, our_organizations_name, supply_date, local_vendor_code,
                                       quantity, amount_with_vat, amount_without_vat, supplier_name, supplier_code, product_name))

        query_update_is_valid = """
        UPDATE ordered_goods_from_buyers
        SET is_valid = False
        WHERE guid = ANY($1::varchar[])
        AND is_valid = True
        """
        query_to_insert = """
        INSERT INTO ordered_goods_from_buyers (guid, document_number, document_created_at, update_document_datetime, event_status,
                               author_of_the_change, our_organizations_name, supply_date, local_vendor_code,
                               quantity, amount_with_vat, amount_without_vat, supplier_name, supplier_code, product_name, warehouse_id,is_valid)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11,  $12, $13, $14, $15, 1, True); """  # по умолчанию передаём основной склад

        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    await conn.execute(query_update_is_valid, guid_data)
                    await conn.executemany(query_to_insert, data_to_update)
                result = OrderedGoodsFromBuyersResponse(
                    status=201,
                    message="Успешно")
        except asyncpg.PostgresError as e:
            result = OrderedGoodsFromBuyersResponse(
                status=422,
                message="PostgresError",
                details=str(e)
            )
        return result

    async def get_buyer_orders(self, date_from: datetime.date, date_to: datetime.date, in_acceptance: bool) -> List[OrderedGoodsFromBuyersData]:
        if in_acceptance is True:
            query = """
            SELECT * FROM ordered_goods_from_buyers
            WHERE 
                in_acceptance = TRUE;
            """
            async with self.pool.acquire() as conn:
                records = await conn.fetch(query)

        else:
            datetime_from = datetime.datetime.combine(date_from, datetime.time.min)  # 2025-04-06 00:00:00
            datetime_to = datetime.datetime.combine(date_to, datetime.time.max)  # 2025-04-06 23:59:59.999999
            query = """
            SELECT * FROM ordered_goods_from_buyers
            WHERE 
                supply_date BETWEEN $1 AND $2;
            """
            async with self.pool.acquire() as conn:
                records = await conn.fetch(query, datetime_from, datetime_to)

        # Преобразуем записи в Pydantic модели
        return [OrderedGoodsFromBuyersData(**record) for record in records]

    async def update_acceptance_status(self, data: List[IsAcceptanceStatus]):
        data_to_update = [(value.id, value.in_acceptance) for value in data]
        print(data)
        query_update_is_acceptance = """
            UPDATE ordered_goods_from_buyers
            SET in_acceptance = $2
            WHERE id = $1;
        """

        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    await conn.executemany(query_update_is_acceptance, data_to_update)
                result = OrderedGoodsFromBuyersResponse(
                    status=201,
                    message="Успешно")
        except asyncpg.PostgresError as e:
            result = OrderedGoodsFromBuyersResponse(
                status=422,
                message="PostgresError",
                details=str(e)
            )
        return result
