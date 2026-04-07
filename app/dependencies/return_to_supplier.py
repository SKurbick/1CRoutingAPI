from asyncpg import Pool
from fastapi import Depends
from starlette.requests import Request

from app.database.repositories.return_to_supplier import ReturnToSupplierRepository
from app.service.return_to_supplier import ReturnToSupplierService


def get_pool(request: Request) -> Pool:
    return request.app.state.pool


def get_return_to_supplier_repository(pool: Pool = Depends(get_pool)) -> ReturnToSupplierRepository:
    return ReturnToSupplierRepository(pool)


def get_return_to_supplier_service(
    repository: ReturnToSupplierRepository = Depends(get_return_to_supplier_repository),
) -> ReturnToSupplierService:
    return ReturnToSupplierService(repository)
