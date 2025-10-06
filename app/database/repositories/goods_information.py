import datetime
import json
from pprint import pprint
from typing import List, Tuple

import asyncpg
from asyncpg import Pool
from app.models import MetawildsData, AllProductsData, GoodsResponse, ProductInfo


class GoodsInformationRepository:
    def __init__(self, pool: Pool):
        self.pool = pool

    async def get_metawilds_data(self) -> List[MetawildsData]:
        query = """
            SELECT * FROM products WHERE is_kit = TRUE and is_active = TRUE;
        """
        async with self.pool.acquire() as conn:
            result = await conn.fetch(query)

        metawilds_data = []
        for res in result:
            # Преобразуем строку kit_components в словарь
            try:
                kit_components = json.loads(res['kit_components'])
            except (json.JSONDecodeError, TypeError):
                kit_components = {}

            metawilds_data.append(
                MetawildsData(
                    id=res['id'],
                    name=res['name'],
                    kit_components=kit_components
                )
            )

        return metawilds_data

    async def get_all_products_data(self) -> List[AllProductsData]:
        query = """
            SELECT * FROM products WHERE is_active = TRUE;
        """
        async with self.pool.acquire() as conn:
            result = await conn.fetch(query)

        all_products_data = []
        for res in result:
            # Преобразуем строку kit_components в словарь
            try:
                kit_components = json.loads(res['kit_components'])
            except (json.JSONDecodeError, TypeError):
                kit_components = {}

            all_products_data.append(
                AllProductsData(
                    id=res['id'],
                    name=res['name'],
                    photo_link=res['photo_link'],
                    is_kit=res['is_kit'],
                    share_of_kit=res['share_of_kit'],
                    kit_components=kit_components,
                    length=res['length'],
                    width=res['width'],
                    height=res['height'],
                    manager=res['manager'],
                )
            )

        return all_products_data

    async def add_product(self, data: List[AllProductsData]) -> GoodsResponse:
        insert_data: list[Tuple] = []
        insert_query = """
            INSERT INTO products (id, name, is_kit, share_of_kit, kit_components, photo_link, length, width, height, manager)
            VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7, $8, $9, $10)
        """

        for product in data:
            kit_components_json = json.dumps(product.kit_components) if product.kit_components else None
            insert_data.append(
                (product.id, product.name, product.is_kit, product.share_of_kit, kit_components_json, 
                 product.photo_link, product.length, product.width, product.height, product.manager)
            )

        pprint(insert_data)
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction() as transaction:
                    await conn.executemany(insert_query, insert_data)

            result = GoodsResponse(
                status=201,
                message="Успешно")
        except asyncpg.PostgresError as e:
            result = GoodsResponse(
                status=422,
                message="PostgresError",
                details=str(e)
            )
        return result
    
    async def update_product_info(self, data: ProductInfo) -> GoodsResponse:
        insert_data = data.model_dump(exclude_unset=True)
        product_id = insert_data.pop("id")

        columns_for_update = []
        values = []

        for i, (key, value) in enumerate(insert_data.items(), start=1):
            columns_for_update.append(f"{key} = ${i}")
            values.append(value)
        
        columns_for_query = ', '.join(columns_for_update)

        check_query = "SELECT id FROM products WHERE id = $1;"
        update_query = (
            "UPDATE products "
            f"SET {columns_for_query} "
            f"WHERE id = ${len(values) + 1};"
        )

        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    # проверяем, есть ли товар с таким id.
                    existing_product = await conn.fetchrow(check_query, product_id)

                    if not existing_product:
                        return GoodsResponse(
                            status=404,
                            message=f"Product data not found. id: {product_id}"
                        )

                    await conn.execute(update_query, *values, product_id)

            result = GoodsResponse(
                status=200,
                message="Успешно")
        except asyncpg.PostgresError as e:
            result = GoodsResponse(
                status=422,
                message="PostgresError",
                details=str(e)
            )
        return result
