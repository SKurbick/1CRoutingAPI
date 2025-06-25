from asyncpg import Pool
from fastapi import Depends
from starlette.requests import Request

from app.service.local_barcode_generation import LocalBarcodeGenerationService
from app.database.repositories.local_barcode_generation import LocalBarcodeGenerationRepository


def get_pool(request: Request) -> Pool:
    """Получение пула соединений из состояния приложения."""
    return request.app.state.pool


def get_local_barcode_generation_repository(pool: Pool = Depends(get_pool)) -> LocalBarcodeGenerationRepository:
    return LocalBarcodeGenerationRepository(pool)


def local_barcode_generation_service(
        repository: LocalBarcodeGenerationRepository = Depends(get_local_barcode_generation_repository)) -> LocalBarcodeGenerationService:
    return LocalBarcodeGenerationService(repository)
