from asyncpg import Pool

from app.models.box_stickers import ImporterView


class ImporterRepository:
    """Взаимодействует с таблицами importers бд"""

    def __init__(self, pool: Pool):
        self.pool = pool

    async def get_all(self) -> list[ImporterView]:
        """Получить список всех импортеров."""
        query = """
        SELECT id, name
        FROM importers 
        ORDER BY name;
        """
        rows = await self.pool.fetch(query)

        return [ImporterView(**row) for row in rows]

    async def upsert_importer(self, name: str) -> int:
        """Реализация возможности добавить нового изготовителя"""
        query = """
            INSERT INTO importers (name) 
            VALUES ($1) 
            ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
            RETURNING id;
        """
        return await self.pool.fetchval(query, name)

    async def get_by_id(self, manufacturer_id: int) -> str:
        """Получить название изготовителя по id"""

        sql = "SELECT name FROM importers WHERE id = $1;"
        name = await self.pool.fetchval(sql, manufacturer_id)
        return name
