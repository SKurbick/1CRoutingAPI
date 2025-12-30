import logging
from typing import Optional

from asyncpg import Pool

from app.models.products_dimensions import ProductDimensions, ProductDimensionsUpdate
from app.models.containers import Container


logger = logging.getLogger(__name__)


class ProductDimensionsRepository:
    def __init__(self, pool: Pool):
        self.pool = pool

    async def get_by_product_id(
        self, 
        product_id: str,
    ) -> Optional[ProductDimensions]:
        """Получить габариты товара по ID."""
        query = """
            SELECT 
                pd.id,
                p.name as product_name,
                pd.product_id,
                pd.length,
                pd.width,
                pd.height,
                pd.volume,
                pd.wb_length,
                pd.wb_width,
                pd.wb_height,
                pd.wb_volume,
                pd.container_id,
                pd.items_per_box,
                pd.created_at,
                pd.updated_at,
                c.id as container__id,
                c.name as container__name,
                c.length as container__length,
                c.width as container__width,
                c.height as container__height,
                c.volume as container__volume,
                c.boxes_per_pallet as container__boxes_per_pallet,
                c.is_active as container__is_active,
                c.created_at as container__created_at,
                c.updated_at as container__updated_at
            FROM products_data pd
            LEFT JOIN products p ON pd.product_id = p.id
            LEFT JOIN containers c ON pd.container_id = c.id
            WHERE pd.product_id = $1
        """

        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(query, product_id)

            if not row:
                return None

            data = dict(row)
            container_data = None

            if data.get("container__id"):
                container_data = Container(
                    id=data.pop("container__id"),
                    name=data.pop("container__name"),
                    length=data.pop("container__length"),
                    width=data.pop("container__width"),
                    height=data.pop("container__height"),
                    volume=data.pop("container__volume"),
                    boxes_per_pallet=data.pop("container__boxes_per_pallet"),
                    is_active=data.pop("container__is_active"),
                    created_at=data.pop("container__created_at"),
                    updated_at=data.pop("container__updated_at")
                )

            return ProductDimensions(
                **data,
                container=container_data
            )
        except Exception as e:
            logger.error(f"Error getting product dimensions for {product_id}: {e}")
            return None

    async def update(
        self, 
        product_id: str, 
        product_data: ProductDimensionsUpdate
    ) -> Optional[ProductDimensions]:
        """Обновить габариты товара"""
        product_dict = product_data.model_dump(exclude_unset=True, exclude_none=True)

        if not product_dict:
            return await self.get_by_product_id(product_id)

        set_parts = []
        values = []
        param_counter = 1

        for field, value in product_dict.items():
            set_parts.append(f"{field} = ${param_counter}")
            values.append(value)
            param_counter += 1

        values.append(product_id)

        query = f"""
            UPDATE products_data
            SET {', '.join(set_parts)}, updated_at = CURRENT_TIMESTAMP
            WHERE product_id = ${param_counter}
            RETURNING 
                id,
                product_id,
                length,
                width,
                height,
                volume,
                wb_length,
                wb_width,
                wb_height,
                wb_volume,
                container_id,
                items_per_box,
                created_at,
                updated_at
        """

        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    await conn.execute(query, *values)

            return await self.get_by_product_id(product_id)
        except Exception as e:
            logger.error(f"Error updating product dimensions for {product_id}: {e}")
            return None

    async def get_all(
        self
    ) -> list[ProductDimensions]:
        """Получить все габариты с фильтрами."""
        query = f"""
            SELECT
                pd.id,
                p.name as product_name,
                pd.product_id,
                pd.length,
                pd.width,
                pd.height,
                pd.volume,
                pd.wb_length,
                pd.wb_width,
                pd.wb_height,
                pd.wb_volume,
                pd.container_id,
                pd.items_per_box,
                pd.created_at,
                pd.updated_at,
                c.id as container__id,
                c.name as container__name,
                c.length as container__length,
                c.width as container__width,
                c.height as container__height,
                c.volume as container__volume,
                c.boxes_per_pallet as container__boxes_per_pallet,
                c.is_active as container__is_active,
                c.created_at as container__created_at,
                c.updated_at as container__updated_at
            FROM products_data pd
            LEFT JOIN products p ON pd.product_id = p.id
            LEFT JOIN containers c ON pd.container_id = c.id
            ORDER BY pd.updated_at DESC
        """

        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query)

            if not rows:
                return []

            result = []
            for row in rows:
                data = dict(row)

                container_data = None

                if data.get("container__id"):
                    container_data = Container(
                        id=data.pop("container__id"),
                        name=data.pop("container__name"),
                        length=data.pop("container__length"),
                        width=data.pop("container__width"),
                        height=data.pop("container__height"),
                        volume=data.pop("container__volume"),
                        boxes_per_pallet=data.pop("container__boxes_per_pallet"),
                        is_active=data.pop("container__is_active"),
                        created_at=data.pop("container__created_at"),
                        updated_at=data.pop("container__updated_at")
                    )

                result.append(ProductDimensions(
                    **data,
                    container=container_data
                ))

            return result
        except Exception as e:
            logger.error(f"Error getting all product dimensions: {e}")
            return []
