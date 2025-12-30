from typing import Optional
import logging

from asyncpg import Pool

from app.models.containers import Container, ContainerCreate, ContainerUpdate


logger = logging.getLogger(__name__)


class ContainerRepository:
    def __init__(self, pool: Pool):
        self.pool = pool

    async def get_all(
        self,
        is_active: Optional[bool] = True
    ) -> list[Container]:
        query = """
            SELECT
                id,
                name,
                length,
                width,
                height,
                volume,
                boxes_per_pallet,
                is_active,
                created_at,
                updated_at
            FROM containers 
            WHERE is_active = $1
            ORDER BY created_at DESC
        """
        
        rows = await self.pool.fetch(query, is_active)
        return [Container(**dict(row)) for row in rows] if rows else []

    async def get_by_id(self, container_id: int) -> Optional[Container]:
        query = """
            SELECT
                id,
                name,
                length,
                width,
                height,
                volume,
                boxes_per_pallet,
                is_active,
                created_at,
                updated_at
            FROM containers WHERE id = $1
        """

        row = await self.pool.fetchrow(query, container_id)
        return Container(**dict(row)) if row else None

    async def create(self, container: ContainerCreate) -> Container:
        query = """
            INSERT INTO containers (
                name, length, width, height, boxes_per_pallet
            ) VALUES (
                $1, $2, $3, $4, $5
            )
            RETURNING *
        """
        values = (
            container.name,
            container.length,
            container.width,
            container.height,
            container.boxes_per_pallet
        )

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                row = await conn.fetchrow(query, *values)

        return Container(**dict(row)) if row else None

    async def update(
        self,
        container_id: int,
        container: ContainerUpdate
    ) -> Optional[Container]:
        update_fields = []
        values = []
        param_counter = 1

        container_dict = container.model_dump(exclude_unset=True)

        for field, value in container_dict.items():
            if value is not None:
                update_fields.append(f"{field} = ${param_counter}")
                values.append(value)
                param_counter += 1

        if not update_fields:
            return await self.get_by_id(container_id)

        values.append(container_id)
        container_id_position = param_counter

        query = f"""
            UPDATE containers
            SET {', '.join(update_fields)}
            WHERE id = ${container_id_position}
            RETURNING *
        """

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                row = await conn.fetchrow(query, *values)

        return Container(**dict(row)) if row else None

    async def delete(self, container_id: int) -> bool:
        query = "DELETE FROM containers WHERE id = $1"

        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    await self.pool.execute(query, container_id)

            return True
        except Exception as e:
            logger.error(f"Error deleting container: {e}")
            return False
