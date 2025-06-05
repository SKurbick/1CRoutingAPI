import datetime
from typing import List

from app.models import OrderedGoodsFromBuyersUpdate
from app.database.repositories import OrderedGoodsFromBuyersRepository
from app.models.ordered_goods_from_buyers import OrderedGoodsFromBuyersResponse, OrderedGoodsFromBuyersData


class OrderedGoodsFromBuyersService:
    def __init__(
            self,
            ordered_goods_from_buyers_repository: OrderedGoodsFromBuyersRepository,
    ):
        self.ordered_goods_from_buyers_repository = ordered_goods_from_buyers_repository

    async def create_data(self, data: List[OrderedGoodsFromBuyersUpdate]) -> OrderedGoodsFromBuyersResponse:
        result = await self.ordered_goods_from_buyers_repository.update_data(data)
        return result

    async def get_buyer_orders(self, date_from: datetime.date, date_to: datetime.date) -> List[OrderedGoodsFromBuyersData]:
        result = await self.ordered_goods_from_buyers_repository.get_buyer_orders(date_from=date_from, date_to=date_to)
        return result
