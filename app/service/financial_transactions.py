from typing import List

from app.models import IncomeOnBankAccountUpdate
from app.database.repositories import FinancialTransactionsRepository
from app.models.financial_transactions import FinancialTransactionsResponse, WriteOffOfNonCashFunds, CashDisbursementOrder


class IncomeOnBankAccountService:
    def __init__(
            self,
            financial_transactions_repository: FinancialTransactionsRepository,
    ):
        self.financial_transactions_repository = financial_transactions_repository

    async def add_income_on_bank_account(self, data: List[IncomeOnBankAccountUpdate]) -> FinancialTransactionsResponse:
        result = await self.financial_transactions_repository.update_data(data)
        return result



    async def add_data_by_write_off_of_non_cash_funds(self, data: List[WriteOffOfNonCashFunds]) -> FinancialTransactionsResponse:
        result = await self.financial_transactions_repository.add_data_by_write_off_of_non_cash_funds(data)
        return result

    async def add_data_cash_disbursement_order(self, data: List[CashDisbursementOrder]) -> FinancialTransactionsResponse:
        result = await self.financial_transactions_repository.add_data_cash_disbursement_order(data)
        return result