from typing import List

from app.models import IncomeOnBankAccountUpdate, GoodsResponse
from app.database.repositories import GoodsInformationRepository
from app.models import MetawildsData, AllProductsData, ProductInfo, GoodsResponse, ProductCreate, ProductUpdate


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

    async def add_products_with_id(self, data: List[AllProductsData]) -> GoodsResponse:
        result = await self.goods_information_repository.add_products_auto_id(data, auto_id=False)
        return result

    async def add_products_without_id(self, data: ProductCreate) -> GoodsResponse:
        result = await self.goods_information_repository.add_products_auto_id(data, auto_id=True)
        return result

    async def update_product(self, id: str, data: ProductUpdate) -> GoodsResponse:
        return await self.goods_information_repository.update_product(id, data)

    async def delete_product(self, id: str) -> GoodsResponse:
        return await self.goods_information_repository.delete_product(id)

    async def update_product_info(self, data: ProductInfo) -> GoodsResponse:
        result = await self.goods_information_repository.update_product_info(data)
        return result
