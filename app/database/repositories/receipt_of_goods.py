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
            data_to_update.append(
                (res_data.document_number,
                 res_data.date,
                 res_data.local_vendor_code,
                 res_data.quantity,
                 res_data.amount_with_vat,
                 res_data.amount_without_vat,
                 res_data.supplier_name,
                 res_data.supplier_code,
                 res_data.update_document_datetime,
                 res_data.author_of_the_change,
                 res_data.our_organizations_name))

        pprint(data_to_update)
        query = """
        INSERT INTO supply_to_sellers_warehouse (document_number,
                                                date,
                                                local_vendor_code,
                                                quantity,
                                                amount_with_vat,
                                                amount_without_vat,
                                                supplier_name,
                                                supplier_code,
                                                update_document_datetime,
                                                author_of_the_change,
                                                our_organizations_name)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        """
        async with self.pool.acquire() as conn:
            await conn.executemany(query, data_to_update)
