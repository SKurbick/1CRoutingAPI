import datetime
import json
from pprint import pprint
from typing import List, Tuple

import asyncpg
from asyncpg import Pool
from app.models import ShipmentOfGoodsUpdate
from app.models.shipment_of_goods import ShipmentOfGoodsResponse, ShipmentParamsData, ReserveOfGoodsCreate, ReserveOfGoodsResponse, ShippedGoods, ReservedData, \
    DeliveryType, ShippedGoodsByID


class ShipmentOfGoodsRepository:
    def __init__(self, pool: Pool):
        self.pool = pool

    async def add_shipped_goods_by_id(self, data: List[ShippedGoodsByID]) -> ShipmentOfGoodsResponse:
        pprint(data)
        update_query = """
            UPDATE product_reserves as pr
            SET shipped =  pr.shipped + $2,
            is_fulfilled = $3 
            WHERE id = $1
            RETURNING id, supply_id;
        """

        values = [
            (
                item.reserve_id,
                item.quantity_shipped,
                item.is_fulfilled
            )
            for item in data
        ]
        records = []
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    # Выполняем запрос с возвратом данных
                    for value in values:
                        record = await conn.fetchrow(update_query, *value)
                        records.append(record)

                return ShipmentOfGoodsResponse(
                    status=201,
                    message="Успешно")
        except asyncpg.PostgresError as e:
            return ShipmentOfGoodsResponse(
                status=422,
                message="PostgresError",
                details=str(e)
            )

    async def get_reserved_data(self, is_fulfilled: bool | None, begin_date: datetime.date | None, delivery_type: DeliveryType | None) -> List[ReservedData]:
        query = ("""SELECT 
                    id as reserve_id,
                    product_id,
                    warehouse_id,
                    ordered,
                    shipped,
                    account,
                    delivery_type,
                    supply_id,
                    reserve_date,
                    is_fulfilled,
                    wb_warehouse
                  from product_reserves WHERE 1=1""")
        params = []
        param_count = 1

        if is_fulfilled is not None:
            query += f" AND is_fulfilled = ${param_count}"
            params.append(is_fulfilled)
            param_count += 1

        if begin_date is not None:
            print("begin_date", begin_date, type(begin_date))
            query += f" AND reserve_date::date >= ${param_count}::date"
            params.append(begin_date)
            param_count += 1

        if delivery_type is not None:
            query += f" AND  delivery_type = ${param_count}"
            params.append(delivery_type)
            param_count += 1

        print(query)

        async with self.pool.acquire() as conn:
            select_result = await conn.fetch(query, *params)
        return [ReservedData(**res) for res in select_result]

    async def update_data(self, data: List[ShipmentOfGoodsUpdate]):
        data_to_update: List[Tuple] = []
        for shipment_data in data:
            author = shipment_data.author
            supply_id = shipment_data.supply_id
            product_id = shipment_data.product_id
            warehouse_id = shipment_data.warehouse_id
            delivery_type = shipment_data.delivery_type
            wb_warehouse = shipment_data.wb_warehouse
            account = shipment_data.account
            quantity = shipment_data.quantity
            date = shipment_data.shipment_date
            product_reserves_id = shipment_data.product_reserves_id

            tuple_data = (author, supply_id, product_id, warehouse_id, delivery_type, wb_warehouse, account, quantity, date, False, None, product_reserves_id)
            data_to_update.append(tuple_data)
        pprint(data_to_update)
        query_to_insert = """
        INSERT INTO shipment_of_goods (author, supply_id, product_id, warehouse_id, delivery_type,
                               wb_warehouse, account, quantity, shipment_date, share_of_kit, metawild, product_reserves_id)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12);
        """
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    await conn.executemany(query_to_insert, data_to_update)

            result = ShipmentOfGoodsResponse(
                status=201,
                message="Успешно")
        except asyncpg.PostgresError as e:
            result = ShipmentOfGoodsResponse(
                status=422,
                message="PostgresError",
                details=str(e)
            )
        return result

    async def get_shipment_params(self):
        accounts_query = """ SELECT account_name from seller_account;"""
        products_query = """ SELECT id FROM products;"""
        try:
            async with self.pool.acquire() as conn:
                accounts_rows = await conn.fetch(accounts_query)
                accounts = [row['account_name'] for row in accounts_rows]
                products_rows = await conn.fetch(products_query)
                products = [row['id'] for row in products_rows]
                result = ShipmentParamsData(products=products, accounts=accounts)

        except asyncpg.PostgresError as e:
            result = ShipmentOfGoodsResponse(
                status=422,
                message="PostgresError",
                details=str(e)
            )
        return result

    async def create_reserve(self, data: List[ReserveOfGoodsCreate]) -> List[ReserveOfGoodsResponse]:
        insert_query = """
                INSERT INTO product_reserves (
                    product_id,
                    warehouse_id,
                    ordered,
                    account,
                    delivery_type,
                    reserve_date,
                    supply_id,
                    expires_at,                                        
                    wb_warehouse

                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING 
                    id,
                    supply_id
                """

        # Подготавливаем значения для вставки
        values = [
            (
                item.product_id,
                item.warehouse_id,
                item.ordered,
                item.account,
                item.delivery_type,
                item.reserve_date,
                item.supply_id,
                item.expires_at,
                item.wb_warehouse
            )
            for item in data
        ]
        records = []
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                # Выполняем запрос с возвратом данных
                for value in values:
                    record = await conn.fetchrow(insert_query, *value)
                    records.append(record)
        # Преобразуем результат в список ReserveOfGoodsResponse
        result = [
            ReserveOfGoodsResponse(
                product_reserves_id=return_data["id"],
                supply_id=return_data["supply_id"]  # Добавляем supply_id из связанной транзакции
            )
            for return_data in records
        ]
        print(result)
        return result

    async def add_shipped_goods(self, data: List[ShippedGoods]) -> List[ReserveOfGoodsResponse]:
        pprint(data)
        update_query = """
            UPDATE product_reserves as pr
            SET shipped =  pr.shipped + $2
            WHERE supply_id = $1
            RETURNING id, supply_id;
        """

        values = [
            (
                item.supply_id,
                item.quantity_shipped
            )
            for item in data
        ]
        records = []
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                # Выполняем запрос с возвратом данных
                for value in values:
                    record = await conn.fetchrow(update_query, *value)
                    records.append(record)

        print(records)
        updated_supplies = {r["supply_id"]: r["id"] for r in records if r is not None}

        return [
            ReserveOfGoodsResponse(
                product_reserves_id=updated_supplies.get(item.supply_id, None),
                supply_id=item.supply_id
            )
            for item in data
        ]
