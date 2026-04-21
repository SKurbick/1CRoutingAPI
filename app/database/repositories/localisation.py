

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