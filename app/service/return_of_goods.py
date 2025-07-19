from typing import List

from app.database.repositories import ReturnOfGoodsRepository
from app.models.return_of_goods import ReturnOfGoodsResponse, ReturnOfGoodsData, IncomingReturns


class ReturnOfGoodsService:
    def __init__(
            self,
            return_of_goods_repository: ReturnOfGoodsRepository,
    ):
        self.return_of_goods_repository = return_of_goods_repository

    async def get_return_of_goods(self) -> List[ReturnOfGoodsData]| ReturnOfGoodsResponse:
        result = await self.return_of_goods_repository.get_return_of_goods()
        return result

    async def incoming_returns(self, data:List[IncomingReturns]) ->ReturnOfGoodsResponse:
        result = await self.return_of_goods_repository.incoming_returns(data)
        return result