

from asyncpg import Pool
from app.models.box_stickers import StickerLocalisationData


class LocalisationRepository:
    def __init__(self, pool: Pool):
        self.pool = pool

    async def get_by_product_id(self, product_id: str) -> list[StickerLocalisationData]:
        sql = """
            SELECT
                product_id,
                field_name,
                lang,
                translation
            FROM localisation
            WHERE product_id = $1;
        """

        rows = await self.pool.fetch(sql, product_id)
        return [StickerLocalisationData(**dict(row)) for row in rows]
    

    async def upsert_many(self, items: list[StickerLocalisationData]) -> None:
        if not items:
            return

        sql = """
            INSERT INTO localisation (
                product_id,
                field_name,
                lang,
                translation
            )
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (product_id, field_name, lang) DO UPDATE
            SET
                translation = EXCLUDED.translation,
                updated_at = now();
        """

        rows = [
            (
                item.product_id,
                item.field_name,
                item.lang,
                item.translation,
            )
            for item in items
        ]

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.executemany(sql, rows)