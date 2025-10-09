import json
from pprint import pprint
from typing import List, Tuple

import asyncpg

from app.models import (MetawildsData, AllProductsData, GoodsResponse, 
                        ProductInfo, ProductCreate, ProductUpdate)


class GoodsInformationRepository:
    def __init__(self, pool: asyncpg.Pool):
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

    @staticmethod
    async def get_max_id(conn: asyncpg.Connection) -> int:
        query = r"""
            SELECT id
            FROM products
            WHERE id ~ '^wild\d+$'
            ORDER BY CAST(substring(id, 5) AS INTEGER) DESC
            LIMIT 1;
        """

        # получаем наибольший id в формате "wild1234"
        max_id_row = await conn.fetchrow(query)
        # преобразуем в число. если данных нет, то max_id = 0
        return int(max_id_row["id"].replace("wild", "")) if max_id_row else 0

    async def add_products_auto_id(self, data: List[ProductCreate | AllProductsData], auto_id: bool = False) -> GoodsResponse:
        insert_query = """
            INSERT INTO products (id, name, is_kit, share_of_kit, kit_components, photo_link, length, width, height, manager)
            VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7, $8, $9, $10)
        """

        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction() as transaction:
                    insert_data: List[Tuple] = []
                    
                    if not auto_id:
                        for product in data:
                            kit_components_json = json.dumps(product.kit_components) if product.kit_components else None

                            insert_data.append(
                                (product.id, product.name, product.is_kit, product.share_of_kit, kit_components_json, 
                                product.photo_link, product.length, product.width, product.height, product.manager)
                            )
                    else:
                        max_id = await self.get_max_id(conn)

                        for product in data:
                            max_id += 1
                            product_id = f"wild{max_id}"
                            kit_components_json = json.dumps(product.kit_components) if product.kit_components else None

                            insert_data.append(
                                (product_id, product.name, product.is_kit, product.share_of_kit, kit_components_json, 
                                product.photo_link, product.length, product.width, product.height, product.manager)
                            )

                    await conn.executemany(insert_query, insert_data)

                    pprint(insert_data)

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

    async def delete_product(self, id: str) -> GoodsResponse:
        dependent_tables = [
            ("inventory_transactions", "product_id"),
            ("shipment_of_goods", "product_id"),
            ("product_reserves", "product_id"),
            ("incoming_items", "product_id"),
            ("incoming_returns", "product_id"),
            ("kit_operations", "kit_product_id"),
            ("inventory_checks", "product_id"),
            ("re_sorting_operations", "from_product_id"),
            ("re_sorting_operations", "to_product_id"),
            ("current_balances", "product_id"),
            ("products", "id"),
        ]

        try:
            deleted_counts = {}

            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    check_query = "SELECT id FROM products WHERE id = $1;" 
                    existing_product = await conn.fetchrow(check_query, id)

                    if not existing_product:
                        return GoodsResponse(
                            status=404,
                            message=f"Product data not found",
                            details=f"id: {id}",
                        )

                    for table, column in dependent_tables:
                        query = f"""
                        DELETE FROM {table}
                        WHERE {column} = $1 RETURNING {column};
                        """
                        row = await conn.fetch(query, id)
                        deleted_counts[table] = len(row)

            return GoodsResponse(
                status=200,
                message="Product and all related data successfully deleted",
                details={"deleted_from": deleted_counts}
            )
        except asyncpg.ForeignKeyViolationError as e:
            return GoodsResponse(
                status=409,
                message="Cannot delete product due to existing references",
                details={"error": str(e)}
        )
        except asyncpg.PostgresError as e:
            return GoodsResponse(
                status=422,
                message="Database error occurred",
                details={"error": str(e)}
            )
        except Exception as e:
            pprint(e)
            return GoodsResponse(
                status=500,
                message="Internal server error",
                details={"error": "An unexpected error occurred"}
            )

    async def update_product_info(self, data: ProductInfo) -> GoodsResponse:
        insert_data = data.model_dump(exclude_unset=True)
        product_id = insert_data.pop("id")

        return await self.update_data_to_db(product_id, insert_data)

    async def update_product(self, id: str, data: ProductUpdate) -> GoodsResponse:
        insert_data = data.model_dump(exclude_unset=True)

        return await self.update_data_to_db(id, insert_data)

    async def update_data_to_db(self, id, data) -> GoodsResponse:
        columns_for_update = []
        values = []

        for i, (key, value) in enumerate(data.items(), start=1):
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
                    existing_product = await conn.fetchrow(check_query, id)

                    if not existing_product:
                        return GoodsResponse(
                            status=404,
                            message=f"Product data not found",
                            details=f"id: {id}",
                        )

                    await conn.execute(update_query, *values, id)

                    return GoodsResponse(
                    status=200,
                    message="Успешно")
        except asyncpg.PostgresError as e:
            return GoodsResponse(
                status=422,
                message="PostgresError",
                details=str(e)
            )

    async def get_delete_preview(self, id) -> GoodsResponse:
        dependent_tables = [
            ("inventory_transactions", "product_id"),
            ("shipment_of_goods", "product_id"),
            ("product_reserves", "product_id"),
            ("incoming_items", "product_id"),
            ("incoming_returns", "product_id"),
            ("kit_operations", "kit_product_id"),
            ("inventory_checks", "product_id"),
            ("re_sorting_operations", "from_product_id"),
            ("re_sorting_operations", "to_product_id"),
            ("current_balances", "product_id"),
            ("products", "id"),
        ]

        async with self.pool.acquire() as conn:
            check_query = "SELECT id FROM products WHERE id = $1;" 
            existing_product = await conn.fetchrow(check_query, id)

            if not existing_product:
                return GoodsResponse(
                    status=404,
                    message="Product data not found",
                    details=f"id: {id}",
                )

            union_parts = []

            for table, column in dependent_tables:
                union_parts.append(f"""
                    SELECT '{table}' as table_name, COUNT(*) as record_count 
                    FROM {table} 
                    WHERE {column} = $1
                """)
            
            union_query = " UNION ALL ".join(union_parts)

            results = await conn.fetch(union_query, id)

        deleted_counts = {row["table_name"]: row["record_count"] for row in results}

        return GoodsResponse(
            status=200,
            message="Product and all related data",
            details=deleted_counts,
        )
