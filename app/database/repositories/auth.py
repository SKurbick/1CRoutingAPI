from asyncpg import Pool
from passlib.context import CryptContext
from app.models.auth import KeyIdentifications

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthRepository:
    def __init__(self, pool: Pool):
        self.pool = pool

    async def get_valid_token(self, token: str) -> KeyIdentifications | None:
        async with self.pool.acquire() as conn:
            record = await conn.fetchrow(
                """SELECT * FROM vector_services_api_keys 
                WHERE is_active = TRUE 
                AND service_name = '1CRoutingAPI'"""
            )
            if record and pwd_context.verify(token, record["api_key"]):
                return KeyIdentifications(**record)
            return None

    async def create_token(self, token: str) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO vector_services_api_keys(api_key, is_active, service_name)
                VALUES($1, TRUE, '1CRoutingAPI' )""",
                pwd_context.hash(token)
            )
