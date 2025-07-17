from asyncpg import Pool
from fastapi import Depends
from starlette.requests import Request

from app.service.inventory_transactions import InventoryTransactionsService
from app.database.repositories.inventory_transactions import InventoryTransactionsRepository

def get_pool(request: Request) -> Pool:
    """Получение пула соединений из состояния приложения."""
    return request.app.state.pool


def get_inventory_transactions_repository(pool: Pool = Depends(get_pool)) -> InventoryTransactionsRepository:
    return InventoryTransactionsRepository(pool)


def get_inventory_transactions_service(repository: InventoryTransactionsRepository = Depends(get_inventory_transactions_repository)) -> InventoryTransactionsService:
    return InventoryTransactionsService(repository)
