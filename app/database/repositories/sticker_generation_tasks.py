



from asyncpg import Pool

from app.models.box_stickers import GenerationStatus, StickerGenerationTaskResult, StickerType


class StickerGenerationTasksRepository:
    
    def __init__(self, pool: Pool):
        self.pool = pool

    async def get_by_unique_key(self, product_id: str, sticker_type: StickerType, template_hash: str) -> StickerGenerationTaskResult | None:
        sql = """
            SELECT
                id AS task_id,
                generation_status,
                document_path,
                generation_task_id,
                error_message
            FROM sticker_generation_tasks
            WHERE product_id = $1
              AND sticker_type = $2
              AND template_hash = $3;
        """

        row = await self.pool.fetchrow(
            sql,
            product_id,
            sticker_type.value,
            template_hash,
        )

        if not row:
            return None

        data = dict(row)

        return StickerGenerationTaskResult(
            task_id=data["task_id"],
            generation_status=GenerationStatus(data["generation_status"]),
            document_path=data["document_path"],
            generation_task_id=data.get("generation_task_id"),
            error_message=data.get("error_message"),
        )
    
    async def create_task (self, product_id: str, sticker_type: StickerType, hash: str, path: str, task_id: str):
        sql = """
            INSERT INTO sticker_generation_tasks (
                product_id,
                sticker_type,
                template_hash,
                generation_status,
                generation_task_id,
                document_path
            )
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING
                id AS task_id,
                generation_status,
                document_path,
                generation_task_id,
                error_message;
        """
        row = await self.pool.fetchrow(
            sql,
            product_id,
            sticker_type,
            hash,
            GenerationStatus.PENDING.value,
            task_id,
            path,
        )
        data = dict(row)
        return StickerGenerationTaskResult(
            task_id=data["task_id"],
            generation_status=GenerationStatus(data["generation_status"]),
            document_path=data["document_path"],
            generation_task_id=data.get("generation_task_id"),
            error_message=data.get("error_message"),
        )
    

    async def get_by_id(self, task_id: int) -> StickerGenerationTaskResult | None:
        sql = """
            SELECT
                id AS task_id,
                generation_status,
                document_path,
                generation_task_id,
                error_message
            FROM sticker_generation_tasks
            WHERE id = $1;
        """
        row = await self.pool.fetchrow(sql, task_id)
        if not row:
            return None

        data = dict(row)
        return StickerGenerationTaskResult(
            task_id=data["task_id"],
            generation_status=GenerationStatus(data["generation_status"]),
            document_path=data["document_path"],
            generation_task_id=data.get("generation_task_id"),
            error_message=data.get("error_message"),
        )