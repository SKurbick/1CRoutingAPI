from asyncpg import Pool
from fastapi import Depends, Request

from app.database.repositories import ContainerRepository
from app.service.containers import ContainerService


def get_pool(request: Request) -> Pool:
    """Получение пула соединений из состояния приложения."""
    return request.app.state.pool


def get_container_repository(
    db: Pool = Depends(get_pool)
) -> ContainerRepository:
    return ContainerRepository(db)


def get_container_service(
    container_repo: ContainerRepository = Depends(get_container_repository)
) -> ContainerService:
    return ContainerService(container_repo)
