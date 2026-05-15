from asyncpg import Pool

from app.models.box_stickers import CertificationType, StickerType, StickerUserTemplateData


class StickerUserDataRepository:
    def __init__(self, pool: Pool):
        self.pool = pool

    async def get_last(self, product_id: str) -> StickerUserTemplateData | None:
        """Возвращает последний пользовательский ввод"""
        sql = """
            SELECT
                product_id,
                sticker_type,
                proforma_number,
                items_per_box,
                total_boxes,
                produced_in,
                gross_weight,
                net_weight,
                box_length,
                box_width,
                box_height,
                certification_type
            FROM sticker_user_data
            WHERE product_id = $1
        """
        row = await self.pool.fetchrow(sql, product_id)
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
            gross_weight=data.get("gross_weight"),
            net_weight=data.get("net_weight"),
            box_length=data.get("box_length"),
            box_width=data.get("box_width"),
            box_height=data.get("box_height"),
            certification_type=(
                CertificationType(data["certification_type"]) 
                if data.get("certification_type") else None
            ),
        )
    
    async def upsert(self, data: StickerUserTemplateData) -> None:
        sql = """
            INSERT INTO sticker_user_data (
                product_id, sticker_type, proforma_number, items_per_box,
                total_boxes, gross_weight, net_weight, 
                box_length, box_width, box_height, certification_type
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            ON CONFLICT (product_id, sticker_type) DO UPDATE
            SET
                proforma_number = EXCLUDED.proforma_number,
                items_per_box = EXCLUDED.items_per_box,
                total_boxes = EXCLUDED.total_boxes,
                gross_weight = EXCLUDED.gross_weight,
                net_weight = EXCLUDED.net_weight,
                box_length = EXCLUDED.box_length,
                box_width = EXCLUDED.box_width,
                box_height = EXCLUDED.box_height,
                certification_type = EXCLUDED.certification_type,
                updated_at = now();
            """

        await self.pool.execute(
            sql,
            data.product_id,
            data.sticker_type.value,
            data.proforma_number,
            data.items_per_box,
            data.total_boxes,
            data.gross_weight,
            data.net_weight,
            data.box_length,
            data.box_width,
            data.box_height,
            data.certification_type.value if data.certification_type else None
        )