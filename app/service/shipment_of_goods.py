from typing import List

from app.models import ShipmentOfGoodsUpdate
from app.database.repositories import ShipmentOfGoodsRepository
from app.models.shipment_of_goods import ShipmentOfGoodsResponse, ShipmentParamsData, ReserveOfGoodsResponse, ReserveOfGoodsCreate, ShippedGoods, DeliveryType


class ShipmentOfGoodsService:
    def __init__(
            self,
            shipment_of_goods_repository: ShipmentOfGoodsRepository,
    ):
        self.shipment_of_goods_repository = shipment_of_goods_repository

    async def create_data(self, data: List[ShipmentOfGoodsUpdate], delivery_type: DeliveryType) -> ShipmentOfGoodsResponse:
        result = await self.shipment_of_goods_repository.update_data(data)
        if result.status == 201:
            match delivery_type: # запрос для 1С
                case DeliveryType.FBO:
                    # todo обработка данных по 1С
                    print("ФБО (через match-case)")
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
