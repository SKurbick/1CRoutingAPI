from pprint import pprint
from typing import List

from app.database.repositories import ReturnOfGoodsRepository
from app.dependencies.config import settings
from app.infrastructure.ONE_C import ONECRouting
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
        if result.status == 201:
            # отправка данных в 1с
            await self.add_data_on_one_c(data=data)
        return result

    async def add_data_on_one_c(self, data:List[IncomingReturns]):
        one_c_database_data = await self.return_of_goods_repository.get_incoming_data_for_one_c(data)
        one_c_connect = ONECRouting(base_url=settings.ONE_C_BASE_URL, password=settings.ONE_C_PASSWORD, login=settings.ONE_C_LOGIN)
        await one_c_connect.goods_returns(data=one_c_database_data)