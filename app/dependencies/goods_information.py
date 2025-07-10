from asyncpg import Pool
from fastapi import Depends
from starlette.requests import Request

from app.service.goods_information import GoodsInformationService
from app.database.repositories.goods_information import GoodsInformationRepository


def get_pool(request: Request) -> Pool:
    """Получение пула соединений из состояния приложения."""
    return request.app.state.pool


def get_goods_information_repository(pool: Pool = Depends(get_pool)) -> GoodsInformationRepository:
    return GoodsInformationRepository(pool)


def get_goods_information_service(repository: GoodsInformationRepository = Depends(get_goods_information_repository)) -> GoodsInformationService:
    return GoodsInformationService(repository)
