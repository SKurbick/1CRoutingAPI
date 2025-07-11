import datetime
import json
from typing import List, Tuple

import asyncpg
from asyncpg import Pool
from app.models import MetawildsData, AllProductsData


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
                    kit_components=kit_components
                )
            )

        return all_products_data
