from fastapi import Depends, Header
from app.service.auth import TokenService


async def verify_service_token(
        x_service_token: str = Header(..., alias="X-Service-Token"),
        token_service: TokenService = Depends(TokenService.get_service)
) -> None:
    await token_service.authenticate(x_service_token)
