from typing import List

from app.models import OrderedGoodsFromBuyersUpdate
from app.database.repositories import OrderedGoodsFromBuyersRepository
from app.models.ordered_goods_from_buyers import OrderedGoodsFromBuyersResponse


class OrderedGoodsFromBuyersService:
    def __init__(
            self,
            ordered_goods_from_buyers_repository: OrderedGoodsFromBuyersRepository,
    ):
        self.ordered_goods_from_buyers_repository = ordered_goods_from_buyers_repository

    async def create_data(self, data: List[OrderedGoodsFromBuyersUpdate]) -> OrderedGoodsFromBuyersResponse:
        resul = await self.ordered_goods_from_buyers_repository.update_data(data)
        return resul
