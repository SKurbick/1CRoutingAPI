from fastapi import Depends, Header, Security
from app.service.auth import AuthService
from app.database.repositories.auth import AuthRepository
from asyncpg import Pool
from fastapi import Depends
from starlette.requests import Request


def get_pool(request: Request) -> Pool:
    """Получение пула соединений из состояния приложения."""
    return request.app.state.pool


def get_auth_repository(pool: Pool = Depends(get_pool)) -> AuthRepository:
    return AuthRepository(pool)


def get_auth_service(repository: AuthRepository = Depends(get_auth_repository)) -> AuthService:
    return AuthService(repository)


async def verify_service_token(
        x_service_token: str = Header(..., alias="X-Service-Token"),
        token_service: AuthService = Depends(get_auth_service)
) -> None:
    await token_service.authenticate(x_service_token)


# core/security.py
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()


async def verify_token(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        token_service: AuthService = Depends(get_auth_service)

) -> str:
    token = credentials.credentials
    await token_service.authenticate(token)
    return token
    # Ваша логика проверки токена из БД
    # if not is_valid_token(token):  # Замените на свою функцию
    #     raise HTTPException(401, "Invalid token")
    # return token
