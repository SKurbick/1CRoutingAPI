from typing import List

from asyncpg import Pool

from app.models.cash_flow_writeoff import CashFlowWriteoff


class CashFlowWriteoffRepository:
    def __init__(self, pool: Pool):
        self.pool = pool

    async def update_data(self, records: List[CashFlowWriteoff]) -> None:
        guid_list = [r.guid for r in records]

        query_update_is_valid = """
        UPDATE cash_flow_writeoffs
        SET is_valid = False
        WHERE guid = ANY($1::varchar[])
        AND is_valid = True
        """

        query_insert = """
        INSERT INTO cash_flow_writeoffs
            (guid, document_number, date, operation_type, organization,
             operation, item_cash_flow, expense_item, amount_vat, amount,
             author, currency, payment_purpose, event_status, bank_status, bank_account, is_valid)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, True)
        """

        data_to_insert = [
            (
                r.guid,
                r.document_number,
                r.date,
                r.operation_type,
                r.organization,
                r.operation,
                pd.item_cash_flow,
                r.expense_item,
                pd.amount_vat,
                pd.amount,
                r.author,
                r.currency,
                r.payment_purpose,
                r.event_status,
                r.bank_status,
                r.bank_account,
            )
            for r in records
            for pd in r.payment_descriptions
        ]

        async with self.pool.acquire() as conn:
            await conn.execute(query_update_is_valid, guid_list)
            await conn.executemany(query_insert, data_to_insert)
