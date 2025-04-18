from pprint import pprint
from pprint import pprint
from typing import List, Tuple

from asyncpg import Pool
from app.models import IncomeOnBankAccountUpdate


class IncomeOnBankAccountRepository:
    def __init__(self, pool: Pool):
        self.pool = pool

    async def update_data(self, data: List[IncomeOnBankAccountUpdate]):
        data_to_update: List[Tuple] = []

        for res_data in data:
            data_to_update.append(
                (res_data.guid,
                 res_data.payment_receipt_date,
                 res_data.document_created_at,
                 res_data.legal_entity,
                 res_data.receipt_account,
                 res_data.bank,
                 res_data.counterparty_name,
                 res_data.counterparty_inn,
                 res_data.amount,
                 res_data.vat,
                 res_data.payment_purpose,
                 res_data.payment_number,
                 res_data.document_number_1c))

        pprint(data_to_update)
        query = """
        INSERT INTO income_on_bank_account    ( guid,
                                                payment_receipt_date,
                                                document_created_at,
                                                legal_entity,
                                                receipt_account,
                                                bank,
                                                counterparty_name,
                                                counterparty_inn,
                                                amount,
                                                vat,
                                                payment_purpose,
                                                payment_number,
                                                document_number_1c)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
        """
        async with self.pool.acquire() as conn:
            await conn.executemany(query, data_to_update)
