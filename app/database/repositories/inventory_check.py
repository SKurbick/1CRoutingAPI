import datetime
from pprint import pprint
from typing import List, Tuple

import asyncpg
from asyncpg import Pool, UniqueViolationError
from app.models import InventoryCheckUpdate, ITGroupData
from app.models.inventory_check import InventoryCheckResponse, InventoryData, IDGroupData
from app.models.inventory_transactions import InventoryTransactionsResponse, ProductGroupData


class InventoryCheckRepository:
    def __init__(self, pool: Pool):
        self.pool = pool

    async def get_inventory_data(self, date_from, date_to):
        try:
            datetime_from = datetime.datetime.combine(date_from, datetime.time.min)  # 2025-04-06 00:00:00
            datetime_to = datetime.datetime.combine(date_to, datetime.time.max)  # 2025-04-06 23:59:59.999999

            query = """
                    select  ic.warehouse_id, 
                    ic.product_id,
                    ic.actual_quantity,
                    DATE(ic.check_date) as check_date,
                    ic.author,
                    ic.comment,
                    ic.created_at, it.quantity as difference_in_quantity  from inventory_checks ic 
                    join inventory_transactions it on ic.id = it.inventory_check_id
                    where check_date  BETWEEN $1 AND $2;
                """
            async with self.pool.acquire() as conn:
                records = await conn.fetch(query, datetime_from, datetime_to)
                # Группируем данные по дате
                grouped_data = {}
                for record in records:
                    date = record["check_date"]
                    product_data = InventoryData(
                        warehouse_id=record["warehouse_id"],
                        product_id=record["product_id"],
                        actual_quantity=record["actual_quantity"],
                        author=record["author"],
                        comment=record["comment"],
                        created_at=record["created_at"],
                        difference_in_quantity=record["difference_in_quantity"]
                    )

                    if date not in grouped_data:
                        grouped_data[date] = IDGroupData(
                            date=date,
                            product_group_data=[]
                        )
                    grouped_data[date].product_group_data.append(product_data)

                # Преобразуем словарь в список ITGroupData
                result = list(grouped_data.values())
                pprint(result)
                return result

        except UniqueViolationError as e:
            return InventoryTransactionsResponse(
                status=422,
                message="UniqueViolationError",
                details=str(e)
            )

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
