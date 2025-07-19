from asyncpg import Pool
from fastapi import Depends
from starlette.requests import Request

from app.service.return_of_goods import ReturnOfGoodsService
from app.database.repositories.return_of_goods import ReturnOfGoodsRepository


def get_pool(request: Request) -> Pool:
    """Получение пула соединений из состояния приложения."""
    return request.app.state.pool


def get_return_of_goods_repository(pool: Pool = Depends(get_pool)) -> ReturnOfGoodsRepository:
    return ReturnOfGoodsRepository(pool)


def get_return_of_goods_service(repository: ReturnOfGoodsRepository = Depends(get_return_of_goods_repository)) -> ReturnOfGoodsService:
    return ReturnOfGoodsService(repository)
