from typing import List

from app.models import IncomeOnBankAccountUpdate
from app.database.repositories import GoodsInformationRepository
from app.models import MetawildsData,AllProductsData


class GoodsInformationService:
    def __init__(
            self,
            goods_information_repository: GoodsInformationRepository,
    ):
        self.goods_information_repository = goods_information_repository

    async def get_metawilds_data(self) -> List[MetawildsData]:
        result = await self.goods_information_repository.get_metawilds_data()
        return result

    async def get_all_products_data(self) -> List[AllProductsData]:
        result = await self.goods_information_repository.get_all_products_data()
        return result