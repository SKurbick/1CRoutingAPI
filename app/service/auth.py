from fastapi import HTTPException, status
from app.database.repositories.auth import AuthRepository
from app.models.auth import KeyIdentifications


class AuthService:
    # def __init__(self, repo: AuthRepository):
    #     self.repo = repo

    # @classmethod
    # async def get_service(cls):
    #     return cls(AuthRepository(await db.pool))
    #
    # async def authenticate(self, token: str) -> None:
    #     if not await self.repo.get_valid_token(token):
    #         raise HTTPException(
    #             status_code=status.HTTP_401_UNAUTHORIZED,
    #             detail="Invalid or expired service token",
    #             headers={"WWW-Authenticate": "Bearer"}
    #         )
    def __init__(self, auth_repository: AuthRepository):
        self.auth_repository = auth_repository

    async def authenticate(self, token: str) -> None:
        if not await self.auth_repository.get_valid_token(token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired service token",
                headers={"WWW-Authenticate": "Bearer"}
            )
