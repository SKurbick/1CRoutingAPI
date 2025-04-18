from typing import List

from app.models import IncomeOnBankAccountUpdate
from app.database.repositories import IncomeOnBankAccountRepository


class IncomeOnBankAccountService:
    def __init__(
            self,
            income_on_bank_account_repository: IncomeOnBankAccountRepository,
    ):
        self.income_on_bank_account_repository = income_on_bank_account_repository

    async def create_data(self, data: List[IncomeOnBankAccountUpdate]):
        await self.income_on_bank_account_repository.update_data(data)
