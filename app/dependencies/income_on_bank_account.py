from asyncpg import Pool
from fastapi import Depends
from starlette.requests import Request

from app.service.income_on_bank_account import IncomeOnBankAccountService
from app.database.repositories.income_on_bank_account import IncomeOnBankAccountRepository


def get_pool(request: Request) -> Pool:
    """Получение пула соединений из состояния приложения."""
    return request.app.state.pool


def get_income_on_bank_account_repository(pool: Pool = Depends(get_pool)) -> IncomeOnBankAccountRepository:
    return IncomeOnBankAccountRepository(pool)


def get_income_on_bank_account_service(repository: IncomeOnBankAccountRepository = Depends(get_income_on_bank_account_repository)) -> IncomeOnBankAccountService:
    return IncomeOnBankAccountService(repository)
