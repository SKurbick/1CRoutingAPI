



from asyncpg import Pool

from app.models.box_stickers import GenerationStatus, StickerGenerationTaskResult, StickerType, StickerGenerationTaskView


class StickerGenerationTasksRepository:
    
    def __init__(self, pool: Pool):
        self.pool = pool

    async def get_by_unique_key(self, product_id: str, sticker_type: StickerType, template_hash: str) -> StickerGenerationTaskResult | None:
        sql = """
            SELECT
                id AS task_id,
                generation_status,
                document_path,
                task_uuid,
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
            task_uuid=data.get("task_uuid"),
            error_message=data.get("error_message"),
        )
    
    async def create_task (self, product_id: str, sticker_type: StickerType, hash: str, path: str) ->StickerGenerationTaskResult:
        #TODO: убарть путь к файлу из запроса. Путь будет генерировать сервис генерации
        sql = """
            INSERT INTO sticker_generation_tasks (
                product_id,
                sticker_type,
                template_hash,
                generation_status,
                document_path
            )
            VALUES ($1, $2, $3, $4, $5)
            RETURNING
                id AS task_id,
                generation_status,
                document_path,
                task_uuid,
                error_message;
        """
        row = await self.pool.fetchrow(
            sql,
            product_id,
            sticker_type,
            hash,
            GenerationStatus.PENDING.value,
            path,
        )
        data = dict(row)
        return StickerGenerationTaskResult(
            task_id=data["task_id"],
            generation_status=GenerationStatus(data["generation_status"]),
            document_path=data["document_path"],
            task_uuid=data.get("task_uuid"),
            error_message=data.get("error_message"),
        )
    

    async def get_by_id(self, task_id: int) -> StickerGenerationTaskResult | None:
        sql = """
            SELECT
                id AS task_id,
                generation_status,
                document_path,
                task_uuid,
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
            task_uuid=data.get("task_uuid"),
            error_message=data.get("error_message"),
        )
    
    async def add_user_to_task(self, task_id: int, user_id: int) -> None:
        """Добавляет каждой задаче id пользователя, ее инициировавшего.
        Необходимо для контроля максимального количества задач на каждом пользователе"""

        sql = """
            INSERT INTO sticker_generation_task_users (task_id, user_id)
            VALUES ($1, $2)
            ON CONFLICT (task_id, user_id) DO NOTHING;
        """
        await self.pool.execute(sql, task_id, user_id)


    async def count_active_tasks_by_user(self, user_id: int) -> int:
        """Считает такси в статусе PENDING и PROCESSING на пользователе. Считает активные задачи"""
        sql = """
            SELECT COUNT(*)
            FROM sticker_generation_task_users tu
            JOIN sticker_generation_tasks t ON t.id = tu.task_id
            WHERE tu.user_id = $1
            AND t.generation_status IN ('PENDING', 'PROCESSING');
        """
        return await self.pool.fetchval(sql, user_id)
    

    async def set_processing(self, task_uuid: str) -> None:
        """Обновляет данные о задаче по генерации стикера после ответа брокера по задаче"""

        sql = """
            UPDATE sticker_generation_tasks
            SET
                generation_status = $2,
                updated_at = now()
            WHERE task_uuid = $1
            """

        await self.pool.execute(
            sql,
            task_uuid,
            GenerationStatus.PROCESSING.value,
        )

    async def update_task_result(
            self, 
            task_uuid: str, 
            status: GenerationStatus, 
            document_path: str | None = None, 
            error_message: str | None = None
        ) -> None:
        """Обновляет статус и информацию о выполнении задачи генерации стикера"""

        sql = """
            UPDATE sticker_generation_tasks
            SET
                generation_status = $2,
                document_path = $3,
                error_message = $4,
                updated_at = now()
            WHERE task_uuid = $1
        """

        await self.pool.execute(
            sql,
            task_uuid,
            status,
            document_path,
            error_message
        )
    
    async def get_tasks_list(self, user_id: int | None = None) -> list[StickerGenerationTaskView]:
        """
        Получить список задач по генерации стикеров.
        """
        params = []

        user_filter_condition = ""

        if user_id:
            params.append(user_id)
            user_filter_condition = f" AND user_id = ${len(params)}"

        tasks_users_cte = f"""
            tasks_users AS (
                SELECT
                    task_id,
                    created_at,
                    ROW_NUMBER() OVER (PARTITION BY task_id ORDER BY created_at DESC) AS rn
                FROM sticker_generation_task_users
                WHERE 1=1
                {user_filter_condition}
            )
        """

        all_cte = f"""
            WITH
                {tasks_users_cte}
        """

        query = f"""
            {all_cte}
            SELECT
                sgt.id,
                sgt.product_id,
                sgt.sticker_type,
                sgt.template_hash,
                LOWER(sgt.generation_status) as generation_status,
                sgt.task_uuid,
                sgt.document_path,
                sgt.error_message
            FROM sticker_generation_tasks sgt
            JOIN tasks_users tu ON sgt.id = tu.task_id AND tu.rn = 1
            ORDER BY tu.created_at DESC
        """

        rows = await self.pool.fetch(query, *params)

        return [
            StickerGenerationTaskView(**row) for row in rows
        ]
