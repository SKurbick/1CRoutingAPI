from asyncpg import Pool

from app.models.box_stickers import CertificationType, StickerIndividualUserData


class IndividualUserDataRepository:
    def __init__(self, pool: Pool):
        self.pool = pool


    async def get_last(self, product_id: str) -> StickerIndividualUserData | None:
        """Возвращает последний пользовательский ввод для индивидуального стикера"""
        sql = """
            SELECT
                product_id,
                manufacturer_id,
                name,
                color,
                material,
                importer_details,
                produced_in,
                certification_type,
                production_date
            FROM sticker_user_data_individual
            WHERE product_id = $1;
        """
        row = await self.pool.fetchrow(sql, product_id)
        if not row:
            return None

        data = dict(row)

        return StickerIndividualUserData(
            product_id=data["product_id"],
            manufacturer_id=data.get("manufacturer_id"),
            name=data["name"],
            color=data.get("color"),
            material=data.get("material"),
            importer_details=data["importer_details"],
            produced_in=data.get("produced_in"),
            certification_type=(
                CertificationType(data["certification_type"]) 
                if data.get("certification_type") else None
            ),
            production_date=data["production_date"]
        )
    

    async def upsert(self, data: StickerIndividualUserData) -> None:
        """Сохраняет или обновляет данные индивидуального стикера"""
        
        sql = """
            INSERT INTO sticker_user_data_individual (
                product_id, manufacturer_id, name, color, 
                material, importer_details, produced_in, certification_type, production_date
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT (product_id) DO UPDATE
            SET
                manufacturer_id = EXCLUDED.manufacturer_id,
                name = EXCLUDED.name,
                color = EXCLUDED.color,
                material = EXCLUDED.material,
                importer_details = EXCLUDED.importer_details,
                produced_in = EXCLUDED.produced_in,
                certification_type = EXCLUDED.certification_type,
                production_date = EXCLUDED.production_date;
            """

        await self.pool.execute(
            sql,
            data.product_id,
            data.manufacturer_id,
            data.name,
            data.color,
            data.material,
            data.importer_details,
            data.produced_in,
            data.certification_type.value if data.certification_type else None,
            data.production_date
        )