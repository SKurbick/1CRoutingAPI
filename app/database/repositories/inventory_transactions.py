import datetime
from pprint import pprint
from typing import List, Tuple, Any, Coroutine

import asyncpg
from asyncpg import Pool, UniqueViolationError
from app.models.inventory_transactions import ITGroupData, InventoryTransactionsResponse, ProductGroupData


class InventoryTransactionsRepository:
    def __init__(self, pool: Pool):
        self.pool = pool

    async def group_data(self, date_from, date_to) -> List[ITGroupData] | InventoryTransactionsResponse:
        try:
            datetime_from = datetime.datetime.combine(date_from, datetime.time.min)  # 2025-04-06 00:00:00
            datetime_to = datetime.datetime.combine(date_to, datetime.time.max)  # 2025-04-06 23:59:59.999999

            query = """
                        SELECT 
                            DATE(it.created_at) as "Дата",
                            it.product_id as "ID продукта",
                            SUM(CASE 
                                    WHEN it.transaction_type = 'outgoing' AND it.delivery_type = 'ФБО' AND it.warehouse_id = 1 THEN it.quantity
                                    ELSE 0 
                                END)::INTEGER AS "Отгрузка по ФБО",
                            SUM(CASE 
                                    WHEN it.transaction_type = 'outgoing' AND it.delivery_type = 'ФБС' AND it.warehouse_id = 1 THEN it.quantity
                                    ELSE 0 
                                END)::INTEGER AS "Отгрузка по ФБС",
                            SUM(CASE 
                                    WHEN (it.transaction_type = 'incoming' OR it.transaction_type = 'adjustment') 
                                    AND it.document_guid IS NOT NULL AND it.warehouse_id = 1 THEN it.quantity
                                    ELSE 0 
                                END)::INTEGER AS "Поступления",
                           SUM(CASE 
                                WHEN it.transaction_type in ('kit_disassembly', 'kit_assembly', 'kit_result') 
                                AND it.warehouse_id = 1 THEN it.quantity
                                ELSE 0 
                            END)::INTEGER AS "Участие в сборке/разборе",
                           SUM(CASE 
                                WHEN it.transaction_type = 'incoming' and document_guid is null and delivery_type is null  and it.warehouse_id =1 
                               THEN it.quantity
                                ELSE 0 
                            END)::INTEGER AS "Поступило со склада «Брак»",
                           SUM(CASE 
                                WHEN it.transaction_type = 'outgoing' and document_guid is null and delivery_type is null  and it.warehouse_id =2 
                               THEN it.quantity
                                ELSE 0 
                            END)::INTEGER AS "Перемещен на склад «Брак»",
                           SUM(CASE 
                                WHEN it.transaction_type = 'return'
                               THEN it.quantity
                                ELSE 0 
                            END)::INTEGER AS "Возвраты от клиента",
                           SUM(CASE 
                                WHEN it.transaction_type in ('re_sorting_incoming', 're_sorting_outgoing') and it.warehouse_id=1
                               THEN it.quantity
                                ELSE 0 
                            END)::INTEGER AS "Пересортица",
                               SUM(CASE 
                                WHEN it.transaction_type in ('add_stock_by_client') 
                               THEN it.quantity
                                ELSE 0 
                            END)::INTEGER AS "Редактирование остатка"  
                        FROM 
                            inventory_transactions it
                        WHERE 
                            created_at BETWEEN $1 AND $2
                        GROUP BY 
                            DATE(it.created_at), it.product_id
                        ORDER BY 
                            DATE(it.created_at), it.product_id;
                """

            async with self.pool.acquire() as conn:
                records = await conn.fetch(query, datetime_from, datetime_to)
                # Группируем данные по дате
                grouped_data = {}
                for record in records:
                    date = record["Дата"]
                    product_data = ProductGroupData(
                        product_id=record["ID продукта"],
                        shipment_fbo=record["Отгрузка по ФБО"],
                        shipment_fbs=record["Отгрузка по ФБС"],
                        incoming=record["Поступления"],
                        re_sorting=record["Пересортица"],
                        returns=record["Возвраты от клиента"],
                        moved_to_the_warehouse_defective=record["Перемещен на склад «Брак»"],
                        received_from_the_warehouse_defective=record["Поступило со склада «Брак»"],
                        kit_result=record["Участие в сборке/разборе"],
                        editing_the_remainder = record["Редактирование остатка"]
                    )

                    if date not in grouped_data:
                        grouped_data[date] = ITGroupData(
                            date=date,
                            product_group_data=[]
                        )
                    grouped_data[date].product_group_data.append(product_data)

                # Преобразуем словарь в список ITGroupData
                result = list(grouped_data.values())
                return result

        except UniqueViolationError as e:
            return InventoryTransactionsResponse(
                status=422,
                message="UniqueViolationError",
                details=str(e)
            )

        except asyncpg.PostgresError as e:
            return InventoryTransactionsResponse(
                status=422,
                message="PostgresError",
                details=str(e)
            )
