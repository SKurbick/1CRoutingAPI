from pprint import pprint
from typing import List, Tuple

from asyncpg import Pool
from app.models import ReceiptOfGoodsUpdate


class ReceiptOfGoodsRepository:
    def __init__(self, pool: Pool):
        self.pool = pool

    async def update_data(self, data: List[ReceiptOfGoodsUpdate]):
        data_to_update: List[Tuple] = []

        for res_data in data:
            date = res_data.date
            for wd in res_data.wild_data:
                local_vendor_code = wd.local_vendor_code
                supply_count = wd.count
                data_to_update.append(
                    (date, local_vendor_code, supply_count)
                )
        pprint(data_to_update)
        query = """
        INSERT INTO supply_to_sellers_warehouse (date, local_vendor_code, quantity_in_delivery)
        VALUES ($1, $2, $3)
        ON CONFLICT (date, local_vendor_code) DO UPDATE SET
            quantity_in_delivery = EXCLUDED.quantity_in_delivery
        """
        async with self.pool.acquire() as conn:
            await conn.executemany(query, data_to_update)
