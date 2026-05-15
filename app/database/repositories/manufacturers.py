from asyncpg import Pool


class ManufacturerRepository:

    def __init__(self, pool: Pool):
        self.pool = pool

    async def get_all(self) -> list[dict]:
        """Получить список всех изготовителей для выпадающего списка"""
        query = "SELECT id, name " \
                "FROM manufacturers " \
                "ORDER BY name;"

        return await self.pool.fetch(query)
    
    async def get_or_create(self, name: str) -> int:
        """Реализация возможности добавить нового изготовителя"""
        query = """
            INSERT INTO manufacturers (name) 
            VALUES ($1) 
            ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
            RETURNING id;
        """
        return await self.pool.fetchval(query, name)
    
    async def get_name_by_id(self, manufacturer_id: int) -> str:
        """Получить название изготовителя по id"""
        
        sql = "SELECT name FROM manufacturers WHERE id = $1;"
        name = await self.pool.fetchval(sql, manufacturer_id)
        return name