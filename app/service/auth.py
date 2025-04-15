from fastapi import HTTPException, status
from db.repositories.token_repo import TokenRepository
from db.session import db
from app.models.auth import ServiceToken

class TokenService:
    def __init__(self, repo: TokenRepository):
        self.repo = repo

    @classmethod
    async def get_service(cls):
        return cls(TokenRepository(await db.pool))

    async def authenticate(self, token: str) -> None:
        if not await self.repo.get_valid_token(token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired service token",
                headers={"WWW-Authenticate": "Bearer"}
            )