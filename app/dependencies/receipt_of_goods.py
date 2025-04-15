from asyncpg import Pool
from fastapi import Depends
from starlette.requests import Request

from app.service.receipt_of_goods import ReceiptOfGoodsService
from app.database.repositories.receipt_of_goods import ReceiptOfGoodsRepository


def get_pool(request: Request) -> Pool:
    """Получение пула соединений из состояния приложения."""
    return request.app.state.pool


def get_receipt_of_goods_repository(pool: Pool = Depends(get_pool)) -> ReceiptOfGoodsRepository:
    return ReceiptOfGoodsRepository(pool)


def get_receipt_of_goods_service(repository: ReceiptOfGoodsRepository = Depends(get_receipt_of_goods_repository)) -> ReceiptOfGoodsService:
    return ReceiptOfGoodsService(repository)
