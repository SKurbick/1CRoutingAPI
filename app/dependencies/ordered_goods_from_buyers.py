from asyncpg import Pool
from fastapi import Depends
from starlette.requests import Request

from app.service.ordered_goods_from_buyers import OrderedGoodsFromBuyersService
from app.database.repositories.ordered_goods_from_buyers import OrderedGoodsFromBuyersRepository


def get_pool(request: Request) -> Pool:
    """Получение пула соединений из состояния приложения."""
    return request.app.state.pool


def get_ordered_goods_from_buyers_repository(pool: Pool = Depends(get_pool)) -> OrderedGoodsFromBuyersRepository:
    return OrderedGoodsFromBuyersRepository(pool)


def get_ordered_goods_from_buyers_service(
        repository: OrderedGoodsFromBuyersRepository = Depends(get_ordered_goods_from_buyers_repository)) -> OrderedGoodsFromBuyersService:
    return OrderedGoodsFromBuyersService(repository)
