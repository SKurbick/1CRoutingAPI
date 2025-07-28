from typing import List

from app.models import ShipmentOfGoodsUpdate
from app.database.repositories import ShipmentOfGoodsRepository
from app.models.shipment_of_goods import ShipmentOfGoodsResponse, ShipmentParamsData, ReserveOfGoodsResponse, ReserveOfGoodsCreate, ShippedGoods


class ShipmentOfGoodsService:
    def __init__(
            self,
            shipment_of_goods_repository: ShipmentOfGoodsRepository,
    ):
        self.shipment_of_goods_repository = shipment_of_goods_repository

    async def create_data(self, data: List[ShipmentOfGoodsUpdate]) -> ShipmentOfGoodsResponse:
        result = await self.shipment_of_goods_repository.update_data(data)
        return result

    async def get_shipment_params(self) -> ShipmentParamsData:
        result = await self.shipment_of_goods_repository.get_shipment_params()
        return result

    async def create_reserve(self, data: List[ReserveOfGoodsCreate]) -> List[ReserveOfGoodsResponse]:
        result = await self.shipment_of_goods_repository.create_reserve(data)
        return result

    async def add_shipped_goods(self, data: List[ShippedGoods]) -> List[ReserveOfGoodsResponse]:
        result = await self.shipment_of_goods_repository.add_shipped_goods(data)
        return result
