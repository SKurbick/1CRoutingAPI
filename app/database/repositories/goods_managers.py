from asyncpg import Pool

from app.models.goods_managers import GoodsManager


class GoodsManagerRepository:
    def __init__(self, pool: Pool):
        self.pool = pool

    async def get_all_managers(self) -> list[GoodsManager]:
        query = """
            SELECT id, name
            FROM goods_managers
            ORDER BY name;
        """

        async with self.pool.acquire() as conn:
            result = await conn.fetch(query)

        return [GoodsManager(**row) for row in result]
