from typing import List

from app.models import ShipmentOfGoodsUpdate
from app.database.repositories import ShipmentOfGoodsRepository
from app.models.shipment_of_goods import ShipmentOfGoodsResponse


class ShipmentOfGoodsService:
    def __init__(
            self,
            shipment_of_goods_repository: ShipmentOfGoodsRepository,
    ):
        self.shipment_of_goods_repository = shipment_of_goods_repository

    async def create_data(self, data: List[ShipmentOfGoodsUpdate]) -> ShipmentOfGoodsResponse:
        resul = await self.shipment_of_goods_repository.update_data(data)
        return resul
