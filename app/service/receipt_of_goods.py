from typing import List

from app.models import ReceiptOfGoodsUpdate, AddIncomingReceiptUpdate
from app.database.repositories import ReceiptOfGoodsRepository
from app.models.receipt_of_goods import ReceiptOfGoodsResponse


class ReceiptOfGoodsService:
    def __init__(
            self,
            receipt_of_goods_repository: ReceiptOfGoodsRepository,
    ):
        self.receipt_of_goods_repository = receipt_of_goods_repository

    async def create_data(self, data: List[ReceiptOfGoodsUpdate]) -> ReceiptOfGoodsResponse:
        resul = await self.receipt_of_goods_repository.update_data(data)
        return resul

    async def add_incoming_receipt(self, data: List[AddIncomingReceiptUpdate]) -> ReceiptOfGoodsResponse:
        resul = await self.receipt_of_goods_repository.add_incoming_receipt(data)
        return resul
