from typing import List

import asyncpg
from asyncpg import Pool

from app.models.return_to_supplier import ReturnToSupplierUpdate


class ReturnToSupplierRepository:
    def __init__(self, pool: Pool):
        self.pool = pool

    async def update_data(self, data: List[ReturnToSupplierUpdate]) -> None:
        invalidate_query = """
            UPDATE return_to_supplier_documents
            SET is_valid = FALSE
            WHERE guid = $1
              AND is_valid = TRUE
        """
        insert_document_query = """
            INSERT INTO return_to_supplier_documents (
                guid, supply_guid, document_number, supplier_name, supplier_code,
                our_organizations_name, event_status, author_of_the_change,
                currency, supply_date, update_document_datetime
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            RETURNING id
        """
        insert_item_query = """
            INSERT INTO return_to_supplier_items (
                document_id, local_vendor_code, product_name,
                quantity, amount_with_vat, amount_without_vat
            )
            VALUES ($1, $2, $3, $4, $5, $6)
        """

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                for document in data:
                    await conn.execute(invalidate_query, document.guid)

                    doc_id = await conn.fetchval(
                        insert_document_query,
                        document.guid,
                        document.supply_guid,
                        document.document_number,
                        document.supplier_name,
                        document.supplier_code,
                        document.our_organizations_name,
                        document.event_status,
                        document.author_of_the_change,
                        document.currency,
                        document.supply_date,
                        document.update_document_datetime,
                    )

                    items = [
                        (
                            doc_id,
                            item.local_vendor_code,
                            item.product_name,
                            item.quantity,
                            item.amount_with_vat,
                            item.amount_without_vat,
                        )
                        for item in document.supply_data
                    ]
                    await conn.executemany(insert_item_query, items)
