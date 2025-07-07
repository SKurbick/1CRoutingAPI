from pprint import pprint
from typing import List, Tuple

import asyncpg
from asyncpg import Pool, UniqueViolationError
from app.models import DefectiveGoodsUpdate
from app.models.warehouse_and_balances import DefectiveGoodsResponse, Warehouse, CurrentBalances


class WarehouseAndBalancesRepository:
    def __init__(self, pool: Pool):
        self.pool = pool

    async def add_defective_goods(self, data: List[DefectiveGoodsUpdate]) -> DefectiveGoodsResponse:
        # data_to_update: List[Tuple] = []
        #
        #
        # author
        # supply_id
        # product_id
        # warehouse_id
        # status_id
        # quantity
        # delivery_type
        # transaction_type
        # correction_comment
        # insert_query = """
        # INSERT INTO (
        #
        # )
        # """
        pass

    async def get_warehouses(self) -> List[Warehouse]:
        select_query = """
        SELECT * FROM warehouses;
        """
        async with self.pool.acquire() as conn:
            result = await conn.fetch(select_query)

        return [Warehouse(**res) for res in result]

    async def get_all_product_current_balances(self) -> List[CurrentBalances]:
        select_query = """
        SELECT * FROM current_balances;
        """
        async with self.pool.acquire() as conn:
            result = await conn.fetch(select_query)
        pprint(result)
        return [CurrentBalances(**res) for res in result]
