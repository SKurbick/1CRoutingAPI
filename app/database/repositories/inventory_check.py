from pprint import pprint
from typing import List, Tuple

import asyncpg
from asyncpg import Pool, UniqueViolationError
from app.models import InventoryCheckUpdate
from app.models.inventory_check import InventoryCheckResponse


class InventoryCheckRepository:
    def __init__(self, pool: Pool):
        self.pool = pool

    async def update_data(self, data: InventoryCheckUpdate) -> InventoryCheckResponse:
        data_to_update: List[Tuple] = []

        for stock_data in data.stock_product_data:
            data_to_update.append(
                (data.warehouse_id, stock_data.product_id, stock_data.quantity, data.datetime, data.author, data.comment)
            )

        pprint(data)
        query = """
        INSERT INTO  inventory_checks ( warehouse_id,
                                        product_id,
                                        actual_quantity,
                                        check_date,
                                        author,
                                        comment)
        VALUES ($1, $2, $3, $4, $5, $6)
        """
        try:
            async with self.pool.acquire() as conn:
                await conn.executemany(query, data_to_update)
                result = InventoryCheckResponse(
                    status=201,
                    message="Данные успешно обновлены",

                )

        except UniqueViolationError as e:
            result = InventoryCheckResponse(
                status=422,
                message="UniqueViolationError",
                details=str(e)
            )
        except asyncpg.PostgresError as e:
            result = InventoryCheckResponse(
                status=422,
                message="PostgresError",
                details=str(e)
            )
        print(result)
        return result
