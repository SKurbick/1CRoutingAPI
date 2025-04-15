from typing import List

from app.models import ReceiptOfGoodsUpdate
from app.database.repositories import ReceiptOfGoodsRepository


class ReceiptOfGoodsService:
    def __init__(
            self,
            receipt_of_goods_repository: ReceiptOfGoodsRepository,
    ):
        self.receipt_of_goods_repository = receipt_of_goods_repository

    async def create_data(self, data: List[ReceiptOfGoodsUpdate]):
        await self.receipt_of_goods_repository.update_data(data)
