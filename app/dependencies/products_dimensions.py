from asyncpg import Pool
from fastapi import Depends, Request

from app.database.repositories import ProductDimensionsRepository
from app.service.products_dimensions import ProductDimensionsService
from app.service.containers import ContainerService
from app.dependencies import get_container_service


def get_pool(request: Request) -> Pool:
    """Получение пула соединений из состояния приложения."""
    return request.app.state.pool


def get_product_dimensions_repository(
    db: Pool = Depends(get_pool)
) -> ProductDimensionsRepository:
    return ProductDimensionsRepository(db)


def get_product_dimensions_service(
    product_data_repo: ProductDimensionsRepository = Depends(get_product_dimensions_repository),
    container_service: ContainerService = Depends(get_container_service)
) -> ProductDimensionsService:
    return ProductDimensionsService(
        repository=product_data_repo,
        container_service=container_service
    )
