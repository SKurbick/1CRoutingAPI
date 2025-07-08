from pprint import pprint
from typing import List, Tuple

import asyncpg
from asyncpg import Pool
from app.models import ShipmentOfGoodsUpdate
from app.models.shipment_of_goods import ShipmentOfGoodsResponse, ShipmentParamsData


class ShipmentOfGoodsRepository:
    def __init__(self, pool: Pool):
        self.pool = pool

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
            date = shipment_data.date
            tuple_data = (author, supply_id, product_id, warehouse_id, delivery_type, wb_warehouse, account, quantity, date)
            data_to_update.append(tuple_data)
        pprint(data_to_update)
        query_to_insert = """
        INSERT INTO shipment_of_goods (author, supply_id, product_id, warehouse_id, delivery_type,
                               wb_warehouse, account, quantity, date)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9);
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
