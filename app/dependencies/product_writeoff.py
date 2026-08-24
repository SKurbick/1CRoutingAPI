from fastapi import Depends
from asyncpg import Pool

from app.database.repositories.product_writeoff import ProductWriteoffRepository
from app.dependencies.return_of_goods import get_pool
from app.service.product_writeoff import ProductWriteoffService


def get_product_writeoff_repository(
    pool: Pool = Depends(get_pool),
) -> ProductWriteoffRepository:
    return ProductWriteoffRepository(pool)


def get_product_writeoff_service(
    repository: ProductWriteoffRepository = Depends(get_product_writeoff_repository),
) -> ProductWriteoffService:
    return ProductWriteoffService(repository)
