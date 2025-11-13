from pprint import pprint
from typing import List, Tuple

import asyncpg
from asyncpg import Pool, UniqueViolationError
from app.models import IncomeOnBankAccountUpdate
from app.models.income_on_bank_account import IncomeOnBankAccountResponse, WriteOffOfNonCashFunds


class IncomeOnBankAccountRepository:
    def __init__(self, pool: Pool):
        self.pool = pool

    async def add_data_by_write_off_of_non_cash_funds(self, data: List[WriteOffOfNonCashFunds]) -> IncomeOnBankAccountResponse:
        data_to_update: List[Tuple] = []
        guid_data: List[str] = []

        for write_off_of_non_cash_funds in data:
            for payment_descriptions in write_off_of_non_cash_funds.payment_descriptions:
                guid_data.append(write_off_of_non_cash_funds.guid)
                data_to_update.append(
                    (
                        write_off_of_non_cash_funds.guid,
                        write_off_of_non_cash_funds.counterparty_name,
                        write_off_of_non_cash_funds.counterparty_inn,
                        write_off_of_non_cash_funds.our_organizations_name,
                        write_off_of_non_cash_funds.our_organizations_inn,
                        write_off_of_non_cash_funds.operation_type,
                        write_off_of_non_cash_funds.event_status,
                        write_off_of_non_cash_funds.document_number_1c,
                        write_off_of_non_cash_funds.document_created_at,
                        write_off_of_non_cash_funds.payment_receipt_date,
                        write_off_of_non_cash_funds.payment_number,
                        write_off_of_non_cash_funds.payment_date,
                        write_off_of_non_cash_funds.bank_event_status,
                        write_off_of_non_cash_funds.our_organizations_account,
                        write_off_of_non_cash_funds.receipt_account,
                        write_off_of_non_cash_funds.payment_request_number,
                        write_off_of_non_cash_funds.currency,
                        write_off_of_non_cash_funds.payment_purpose,
                        write_off_of_non_cash_funds.author,
                        payment_descriptions.payment_object,
                        payment_descriptions.amount,
                        payment_descriptions.vat_rate,
                        payment_descriptions.vat)
                )

        pprint(data_to_update)

        query_update_is_valid = """
        UPDATE write_off_of_non_cash_funds
        SET is_valid = False
        WHERE guid = ANY($1::varchar[])
        AND is_valid = True
        """
        query = """
        INSERT INTO write_off_of_non_cash_funds (
                                                guid,
                                                counterparty_name,
                                                counterparty_inn,
                                                our_organizations_name,
                                                our_organizations_inn,
                                                operation_type,
                                                event_status,
                                                document_number_1c,
                                                document_created_at,
                                                payment_receipt_date,
                                                payment_number,
                                                payment_date,
                                                bank_event_status,
                                                our_organizations_account,
                                                receipt_account,
                                                payment_request_number,
                                                currency,
                                                payment_purpose,
                                                author,
                                                payment_object,
                                                amount,
                                                vat_rate,
                                                vat,
                                                is_valid)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, True)
        """
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(query_update_is_valid, guid_data)
                await conn.executemany(query, data_to_update)
                result = IncomeOnBankAccountResponse(
                    status=201,
                    message="Данные успешно обновлены",

                )
                return result

        except UniqueViolationError as e:
            result = IncomeOnBankAccountResponse(
                status=422,
                message="UniqueViolationError",
                details=str(e)
            )
            return result
        except asyncpg.PostgresError as e:
            result = IncomeOnBankAccountResponse(
                status=422,
                message="PostgresError",
                details=str(e)
            )
            print(result)
            return result

    async def update_data(self, data: List[IncomeOnBankAccountUpdate]) -> IncomeOnBankAccountResponse:
        data_to_update: List[Tuple] = []
        guid_data: List[str] = []

        for res_data in data:
            guid_data.append(res_data.guid)
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

        query_update_is_valid = """
        UPDATE income_on_bank_account
        SET is_valid = False
        WHERE guid = ANY($1::varchar[])
        AND is_valid = True
        """

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
                                                document_number_1c,
                                                is_valid)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, True)
        """
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(query_update_is_valid, guid_data)
                await conn.executemany(query, data_to_update)
                result = IncomeOnBankAccountResponse(
                    status=201,
                    message="Данные успешно обновлены",

                )
                return result

        except UniqueViolationError as e:
            result = IncomeOnBankAccountResponse(
                status=422,
                message="UniqueViolationError",
                details=str(e)
            )
            return result
        except asyncpg.PostgresError as e:
            result = IncomeOnBankAccountResponse(
                status=422,
                message="PostgresError",
                details=str(e)
            )
            print(result)
            return result
