import datetime
from pprint import pprint
from typing import List, Tuple, Any, Coroutine

import asyncpg
from asyncpg import Pool, UniqueViolationError
from app.models.inventory_transactions import ITGroupData, InventoryTransactionsResponse, ProductGroupData, AddStockByClientGroupData, AddStockByClient, \
    KitOperationsGroupData, KitOperations, IncomingReturnsTable, IncomingReturnsGroupData, ReSortingOperationGroupData, ReSortingOperation, GoodsReturn


class InventoryTransactionsRepository:
    def __init__(self, pool: Pool):
        self.pool = pool

    async def get_re_sorting_operations(self, date_from, date_to) -> List[ReSortingOperationGroupData] | InventoryTransactionsResponse:
        try:
            datetime_from = datetime.datetime.combine(date_from, datetime.time.min)  # 2025-04-06 00:00:00
            datetime_to = datetime.datetime.combine(date_to, datetime.time.max)  # 2025-04-06 23:59:59.999999

            query = """
                        SELECT 
                            id,
                            from_product_id,
                            to_product_id,
                            warehouse_id,
                            reason,
                            quantity,
                            author,
                            operation_status,
                            created_at,
                            DATE(created_at) as "date"
                        FROM 
                            re_sorting_operations
                        WHERE 
                            created_at BETWEEN $1 AND $2 
                        ORDER BY 
                            DATE(created_at), from_product_id;
                """

            async with self.pool.acquire() as conn:
                records = await conn.fetch(query, datetime_from, datetime_to)
                # Группируем данные по дате
                grouped_data = {}
                for record in records:
                    date = record["date"]
                    product_data = ReSortingOperation(
                        operation_id=record['id'],
                        from_product_id=record['from_product_id'],
                        to_product_id=record['to_product_id'],
                        warehouse_id=record['warehouse_id'],
                        reason = record['reason'],
                        quantity=record['quantity'],
                        author=record['author'],
                        operation_status = record['operation_status'],
                        created_at=record['created_at']
                    )

                    if date not in grouped_data:
                        grouped_data[date] = IncomingReturnsGroupData(
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

    async def get_incoming_returns(self, date_from, date_to) -> List[IncomingReturnsGroupData] | InventoryTransactionsResponse:
        try:
            datetime_from = datetime.datetime.combine(date_from, datetime.time.min)
            datetime_to = datetime.datetime.combine(date_to, datetime.time.max)

            query = """
                SELECT 
                    ir.id,
                    ir.product_id,
                    ir.warehouse_id,
                    ir.quantity,
                    ir.author,
                    ir.created_at,
                    DATE(ir.created_at) as "date",
                    gr.srid,
                    gr.account,
                    gr.barcode,
                    gr.brand,
                    gr.dst_office_address,
                    gr.dst_office_id,
                    gr.nm_id,
                    gr.order_dt,
                    gr.order_id,
                    gr.return_type,
                    gr.shk_id,
                    gr.sticker_id,
                    gr.subject_name,
                    gr.tech_size,
                    gr.reason,
                    gr.is_status_active,
                    gr.created_at as goods_created_at,
                    gr.is_received
                FROM 
                    incoming_returns ir
                LEFT JOIN 
                    goods_returns_dev gr ON ir.id = gr.incoming_return_id
                WHERE 
                    ir.created_at BETWEEN $1 AND $2 
                ORDER BY 
                    DATE(ir.created_at), ir.product_id, ir.id;
            """

            async with self.pool.acquire() as conn:
                records = await conn.fetch(query, datetime_from, datetime_to)

                # Группируем данные по дате и operation_id
                grouped_data = {}
                current_operation_id = None
                current_product_data = None

                for record in records:
                    date = record["date"]
                    operation_id = record["id"]

                    # Создаем новый IncomingReturnsTable при смене operation_id
                    if operation_id != current_operation_id:
                        current_operation_id = operation_id

                        current_product_data = IncomingReturnsTable(
                            operation_id=record['id'],
                            product_id=record['product_id'],
                            warehouse_id=record['warehouse_id'],
                            quantity=record['quantity'],
                            author=record['author'],
                            created_at=record['created_at'],
                            goods_return_data=[]
                        )

                        if date not in grouped_data:
                            grouped_data[date] = IncomingReturnsGroupData(
                                date=date,
                                product_group_data=[]
                            )
                        grouped_data[date].product_group_data.append(current_product_data)

                    # Добавляем GoodsReturn если есть данные из joined таблицы
                    if record['srid'] is not None:
                        goods_return = GoodsReturn(
                            srid=record['srid'],
                            account=record['account'],
                            barcode=record['barcode'],
                            brand=record['brand'],
                            dst_office_address=record['dst_office_address'],
                            dst_office_id=record['dst_office_id'],
                            nm_id=record['nm_id'],
                            order_dt=record['order_dt'],
                            order_id=record['order_id'],
                            return_type=record['return_type'],
                            shk_id=record['shk_id'],
                            sticker_id=record['sticker_id'],
                            subject_name=record['subject_name'],
                            tech_size=record['tech_size'],
                            reason=record['reason'],
                            is_status_active=record['is_status_active'],
                            goods_created_at=record['goods_created_at'],
                            is_received=record['is_received']
                        )
                        current_product_data.goods_return_data.append(goods_return)

                # Преобразуем словарь в список
                result = list(grouped_data.values())
                return result

        except UniqueViolationError as e:
            return InventoryTransactionsResponse(
                status=422,
                message="UniqueViolationError",
                details=str(e)
            )

    async def get_kit_operations(self, date_from, date_to) -> List[KitOperationsGroupData] | InventoryTransactionsResponse:
        try:
            datetime_from = datetime.datetime.combine(date_from, datetime.time.min)  # 2025-04-06 00:00:00
            datetime_to = datetime.datetime.combine(date_to, datetime.time.max)  # 2025-04-06 23:59:59.999999

            query = """
                        SELECT 
                            id,
                            kit_product_id,
                            warehouse_id,
                            operation_type,
                            quantity,
                            status,
                            author,
                            created_at,
                            DATE(created_at) as "date"
                        FROM 
                            kit_operations
                        WHERE 
                            created_at BETWEEN $1 AND $2 
                        ORDER BY 
                            DATE(created_at), kit_product_id;
                """

            async with self.pool.acquire() as conn:
                records = await conn.fetch(query, datetime_from, datetime_to)
                # Группируем данные по дате
                grouped_data = {}
                for record in records:
                    date = record["date"]
                    product_data = KitOperations(
                        operation_id=record['id'],
                        kit_product_id=record['kit_product_id'],
                        warehouse_id=record['warehouse_id'],
                        operation_type=record['operation_type'],
                        quantity=record['quantity'],
                        status=record['status'],
                        author=record['author'],
                        created_at=record['created_at']
                    )

                    if date not in grouped_data:
                        grouped_data[date] = KitOperationsGroupData(
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

    async def get_add_stock_by_client(self, date_from, date_to) -> List[AddStockByClientGroupData] | InventoryTransactionsResponse:
        try:
            datetime_from = datetime.datetime.combine(date_from, datetime.time.min)  # 2025-04-06 00:00:00
            datetime_to = datetime.datetime.combine(date_to, datetime.time.max)  # 2025-04-06 23:59:59.999999

            query = """
                        SELECT 
                            product_id,
                            author,
                            warehouse_id,
                            quantity,
                            correction_comment,
                            DATE(created_at) as "date"
                        FROM 
                            inventory_transactions
                        WHERE 
                            created_at BETWEEN $1 AND $2 and transaction_type = 'add_stock_by_client'
                        ORDER BY 
                            DATE(created_at), product_id;
                """

            async with self.pool.acquire() as conn:
                records = await conn.fetch(query, datetime_from, datetime_to)
                # Группируем данные по дате
                grouped_data = {}
                for record in records:
                    date = record["date"]
                    product_data = AddStockByClient(
                        product_id=record["product_id"],
                        author=record["author"],
                        warehouse_id=record["warehouse_id"],
                        quantity=record["quantity"],
                        correction_comment=record["correction_comment"]
                    )

                    if date not in grouped_data:
                        grouped_data[date] = AddStockByClientGroupData(
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
                                WHEN it.transaction_type = 'outgoing' and document_guid is null and delivery_type is null  and it.warehouse_id = 1
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
                        editing_the_remainder=record["Редактирование остатка"]
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
