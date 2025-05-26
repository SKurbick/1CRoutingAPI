from asyncpg import Pool
from fastapi import Depends
from starlette.requests import Request

from app.service.shipment_of_goods import ShipmentOfGoodsService
from app.database.repositories.shipment_of_goods import ShipmentOfGoodsRepository


def get_pool(request: Request) -> Pool:
    """Получение пула соединений из состояния приложения."""
    return request.app.state.pool


def get_shipment_of_goods_repository(pool: Pool = Depends(get_pool)) -> ShipmentOfGoodsRepository:
    return ShipmentOfGoodsRepository(pool)


def get_shipment_of_goods_service(repository: ShipmentOfGoodsRepository = Depends(get_shipment_of_goods_repository)) -> ShipmentOfGoodsService:
    return ShipmentOfGoodsService(repository)
