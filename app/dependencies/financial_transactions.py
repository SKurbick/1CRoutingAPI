from asyncpg import Pool
from fastapi import Depends
from starlette.requests import Request

from app.service.financial_transactions import IncomeOnBankAccountService
from app.database.repositories.financial_transactions import FinancialTransactionsRepository


def get_pool(request: Request) -> Pool:
    """Получение пула соединений из состояния приложения."""
    return request.app.state.pool


def get_financial_transactions_repository(pool: Pool = Depends(get_pool)) -> FinancialTransactionsRepository:
    return FinancialTransactionsRepository(pool)

def get_financial_transactions_service(repository: FinancialTransactionsRepository = Depends(get_financial_transactions_repository)) -> IncomeOnBankAccountService:
    return IncomeOnBankAccountService(repository)
