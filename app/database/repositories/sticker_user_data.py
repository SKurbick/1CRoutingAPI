from asyncpg import Pool

from app.models.box_stickers import StickerType, StickerUserTemplateData


class StickerUserDataRepository:
    def __init__(self, pool: Pool):
        self.pool = pool

    async def get_last(self, product_id: str, sticker_type: StickerType,) -> StickerUserTemplateData | None:
        sql = """
            SELECT
                product_id,
                sticker_type,
                proforma_number,
                items_per_box,
                total_boxes,
                produced_in,
                importer_id
            FROM sticker_user_data
            WHERE product_id = $1
              AND sticker_type = $2;
        """
        row = await self.pool.fetchrow(sql, product_id, sticker_type.value)
        if not row:
            return None

        data = dict(row)

        return StickerUserTemplateData(
            product_id=data["product_id"],
            sticker_type=StickerType(data["sticker_type"]),
            proforma_number=data.get("proforma_number"),
            items_per_box=data.get("items_per_box"),
            total_boxes=data.get("total_boxes"),
            produced_in=data.get("produced_in"),
            importer_id=data.get("importer_id"),
        )
    
    async def upsert(self, data: StickerUserTemplateData) -> None:
        sql = """
            INSERT INTO sticker_user_data (
                product_id,
                sticker_type,
                proforma_number,
                items_per_box,
                total_boxes,
                produced_in,
                importer_id
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (product_id, sticker_type) DO UPDATE
            SET
                proforma_number = EXCLUDED.proforma_number,
                items_per_box = EXCLUDED.items_per_box,
                total_boxes = EXCLUDED.total_boxes,
                produced_in = EXCLUDED.produced_in,
                importer_id = EXCLUDED.importer_id,
                updated_at = now();
        """

        await self.pool.execute(
            sql,
            data.product_id,
            data.sticker_type.value,
            data.proforma_number,
            data.items_per_box,
            data.total_boxes,
            data.produced_in,
            data.importer_id,
        )