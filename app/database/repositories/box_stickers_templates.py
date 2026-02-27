from asyncpg import Pool

from app.models.box_stickers import BoxStickerTemplate, BoxStickerTemplateShort


class BoxStickersTemplateRepository:
    def __init__(self, pool: Pool):
        self.pool = pool

    async def get_list(self) -> list[BoxStickerTemplateShort]:
        query = """
            SELECT
                article,
                name
            FROM box_stickers_templates
            ORDER BY article;
        """

        rows = await self.pool.fetch(query)

        return [BoxStickerTemplateShort(**row) for row in rows]

    async def get(self, article: str) -> BoxStickerTemplate | None:
        query = """
            SELECT
                article,
                name,
                name_en,
                color,
                color_en,
                gross_weight,
                net_weight,
                box_length,
                box_width,
                box_height,
                items_per_box,
                total_boxes,
                produced_in,
                produced_in_en,
                proforma_number,
                certification_type
            FROM box_stickers_templates
            WHERE article = $1;
        """

        result = await self.pool.fetchrow(query, article) or {}
        return BoxStickerTemplate(**result) if result else None

    async def update(self, template: BoxStickerTemplate) -> None:
        if not template.article:
            raise ValueError("Не задано поле article для сохранения шаблона.")
        
        query = """
            INSERT INTO box_stickers_templates (
                article,
                name,
                name_en,
                color,
                color_en,
                gross_weight,
                net_weight,
                box_length,
                box_width,
                box_height,
                items_per_box,
                total_boxes,
                produced_in,
                produced_in_en,
                proforma_number,
                certification_type
            )
            VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, 
                $11, $12, $13, $14, $15, $16
            )
            ON conflict (article) DO UPDATE
            SET
                name = EXCLUDED.name,
                name_en = EXCLUDED.name_en,
                color = EXCLUDED.color,
                color_en = EXCLUDED.color_en,
                gross_weight = EXCLUDED.gross_weight,
                net_weight = EXCLUDED.net_weight,
                box_length = EXCLUDED.box_length,
                box_width = EXCLUDED.box_width,
                box_height = EXCLUDED.box_height,
                items_per_box = EXCLUDED.items_per_box,
                total_boxes = EXCLUDED.total_boxes,
                produced_in = EXCLUDED.produced_in,
                produced_in_en = EXCLUDED.produced_in_en,
                proforma_number = EXCLUDED.proforma_number,
                certification_type = EXCLUDED.certification_type
        """

        data_to_insert = (
            template.article,
            template.name,
            template.name_en,
            template.color,
            template.color_en,
            template.gross_weight,
            template.net_weight,
            template.box_length,
            template.box_width,
            template.box_height,
            template.items_per_box,
            template.total_boxes,
            template.produced_in,
            template.produced_in_en,
            template.proforma_number,
            template.certification_type,
        )

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(query, *data_to_insert)
