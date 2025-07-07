from asyncpg import Pool
from fastapi import Depends
from starlette.requests import Request

from app.service.warehouse_and_balances import WarehouseAndBalancesService
from app.database.repositories.warehouse_and_balances import WarehouseAndBalancesRepository


def get_pool(request: Request) -> Pool:
    """Получение пула соединений из состояния приложения."""
    return request.app.state.pool


def get_warehouse_and_balances_repository(pool: Pool = Depends(get_pool)) -> WarehouseAndBalancesRepository:
    return WarehouseAndBalancesRepository(pool)


def get_warehouse_and_balances_service(repository: WarehouseAndBalancesRepository = Depends(get_warehouse_and_balances_repository)) -> WarehouseAndBalancesService:
    return WarehouseAndBalancesService(repository)
