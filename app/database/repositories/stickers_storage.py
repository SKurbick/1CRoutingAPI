from asyncpg import Pool

from app.models.box_stickers import BoxSize, CertificationType, StickerProductData


class StickersStorageRepository:
    def __init__(self, pool: Pool):
        self.pool = pool

    
    async def get_by_product_id(self, product_id: str) -> StickerProductData| None: #TODO: net_weight для индивидуальных стикеров. produced_in нет в БД
        sql = """
            SELECT
                product_id,
                name,
                color,
                material,
                gross_weight,
                --net_weight,
                box_length,
                box_width,
                box_height,
                --produced_in,
                certification_type
            FROM stickers_storage
            --WHERE product_id = $1 OR name ILIKE $1
            WHERE product_id = $1
            --ORDER BY product_id;
        """
        row = await self.pool.fetchrow(sql, product_id)
        if not row:
            return None
        product_data=dict(row)
        
        return StickerProductData(
            product_id=product_data["product_id"],
            name=product_data["name"],
            color=product_data.get("color"),
            material=product_data.get("material"),
            gross_weight=float(product_data["gross_weight"]) if product_data.get("gross_weight") else None,
            # net_weight=float(data["net_weight"]) if data.get("net_weight") else None,
            box_size=BoxSize(
                box_length=float(product_data["box_length"]) if product_data.get("box_length") else 0,
                box_width=float(product_data["box_width"]) if product_data.get("box_width") else 0,
                box_height=float(product_data["box_height"]) if product_data.get("box_height") else 0,
            ),
            # produced_in=data.get("produced_in"),
            certification_type=CertificationType(product_data.get("certification_type", "NONE")),
        )
    #сделал аналогично async def get(self, article: str). Возвращает результат только по product_id!
    








