from asyncpg import Pool
from fastapi import Depends
from starlette.requests import Request

from app.service.goods_managers import GoodsManagersService
from app.database.repositories.goods_managers import GoodsManagerRepository


def get_pool(request: Request) -> Pool:
    """Получение пула соединений из состояния приложения."""
    return request.app.state.pool


def get_goods_managers_repository(pool: Pool = Depends(get_pool)) -> GoodsManagerRepository:
    return GoodsManagerRepository(pool)


def get_goods_managers_service(repository: GoodsManagerRepository = Depends(get_goods_managers_repository)) -> GoodsManagersService:
    return GoodsManagersService(repository)
