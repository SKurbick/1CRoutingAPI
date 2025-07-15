from asyncpg import Pool
from fastapi import Depends
from starlette.requests import Request

from app.service.inventory_check import InventoryCheckService
from app.database.repositories.inventory_check import InventoryCheckRepository


def get_pool(request: Request) -> Pool:
    """Получение пула соединений из состояния приложения."""
    return request.app.state.pool


def get_inventory_check_repository(pool: Pool = Depends(get_pool)) -> InventoryCheckRepository:
    return InventoryCheckRepository(pool)


def get_inventory_check_service(repository: InventoryCheckRepository = Depends(get_inventory_check_repository)) -> InventoryCheckService:
    return InventoryCheckService(repository)
