from asyncpg import Pool
from fastapi import Depends
from starlette.requests import Request

from app.service.docs import DocsService
from app.database.repositories.docs import DocsRepository


def get_pool(request: Request) -> Pool:
    """Получение пула соединений из состояния приложения."""
    return request.app.state.pool


def get_docs_repository(pool: Pool = Depends(get_pool)) -> DocsRepository:
    return DocsRepository(pool)


def get_docs_service(repository: DocsRepository = Depends(get_docs_repository)) -> DocsService:
    return DocsService(repository)
