from pprint import pprint
from typing import List, Tuple

from asyncpg import Pool
from app.models import ReceiptOfGoodsUpdate


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
            guid_data.append(guid)
            for supply_data in document_data.supply_data:
                supply_date = supply_data.supply_date
                local_vendor_code = supply_data.local_vendor_code
                quantity = supply_data.quantity
                amount_with_vat = supply_data.amount_with_vat
                amount_without_vat = supply_data.amount_without_vat
                supplier_name = supply_data.supplier_name
                supplier_code = supply_data.supplier_code

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
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(query_to_update, guid_data)
                await conn.executemany(query_to_insert, data_to_update)
