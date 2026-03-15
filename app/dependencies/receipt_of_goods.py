from asyncpg import Pool
from fastapi import Depends
from starlette.requests import Request

from app.service.receipt_of_goods import ReceiptOfGoodsService
from app.database.repositories.receipt_of_goods import ReceiptOfGoodsRepository
from app.database.repositories.wms_receipt_repository import WMSReceiptRepository
from app.service.wms_integration_service import WMSIntegrationService


def get_pool(request: Request) -> Pool:
    """Получение пула соединений из состояния приложения."""
    return request.app.state.pool


def get_receipt_of_goods_repository(pool: Pool = Depends(get_pool)) -> ReceiptOfGoodsRepository:
    return ReceiptOfGoodsRepository(pool)


def get_wms_receipt_repository(pool: Pool = Depends(get_pool)) -> WMSReceiptRepository:
    """Создать WMS Receipt Repository"""
    return WMSReceiptRepository(pool)


def get_wms_integration_service(
    wms_receipt_repo: WMSReceiptRepository = Depends(get_wms_receipt_repository),
    pool: Pool = Depends(get_pool)
) -> WMSIntegrationService:
    """Создать WMS Integration Service"""
    return WMSIntegrationService(
        receipt_repository=wms_receipt_repo,
        pool=pool
    )


def get_receipt_of_goods_service(
    repository: ReceiptOfGoodsRepository = Depends(get_receipt_of_goods_repository),
    wms_service: WMSIntegrationService = Depends(get_wms_integration_service)
) -> ReceiptOfGoodsService:
    return ReceiptOfGoodsService(repository, wms_service)
