import datetime
import json
from collections import defaultdict
from pprint import pprint
from typing import List, Tuple

import asyncpg
from asyncpg import Pool
from app.models import ShipmentOfGoodsUpdate, WriteOffAccordingToFBS
from app.models.shipment_of_goods import ShipmentOfGoodsResponse, ShipmentParamsData, ReserveOfGoodsCreate, ReserveOfGoodsResponse, ShippedGoods, ReservedData, \
    DeliveryType, ShippedGoodsByID, SummReserveData, DeliveryTypeData, CreationWithMovement, ShipmentWithReserveUpdating


class ShipmentOfGoodsRepository:
    def __init__(self, pool: Pool):
        self.pool = pool




    async def write_off_according_to_fbs(self, data: List[WriteOffAccordingToFBS]) ->ShipmentOfGoodsResponse:
        """
        Метод отгрузки товаров по ФБС. Перед списанием товара проверяет СЗ на повтор отгрузки.
        Если хоть одно заявленное к отгрузке СЗ ранее было отгружено, то транзакция откатится и весь массив на списание
        будет не исполнен.
        """
        # собираем сборочные задания для проверки
        # если хоть одно ЗС ранее уже было отгружено, отбиваем ошибку. Так же при условии если СЗ нет в бд
        # в обратно случае устанавливаем все как отгруженные
        # так же устанавливаем отгрузку в shipment_of_goods
        # отбиваем успешный результат
        pass
    async def shipment_with_reserve_updating(
            self,
            data: List[ShipmentWithReserveUpdating]
    ) -> ShipmentOfGoodsResponse:
        """
        Обновляет резервы и создает записи об отгрузке в одной транзакции
        """
        # Подготовка данных для обновления резервов
        update_reserve_query = """
            UPDATE product_reserves as pr
            SET shipped = pr.shipped + $2,
                is_fulfilled = $3 
            WHERE id = $1;
        """

        # Подготовка данных для вставки отгрузок
        insert_shipment_query = """
            INSERT INTO shipment_of_goods 
                (author, supply_id, product_id, warehouse_id, delivery_type,
                 wb_warehouse, account, quantity, shipment_date, 
                 share_of_kit, metawild, product_reserves_id)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12);
        """

        # Подготавливаем значения для обоих запросов
        reserve_values = []
        shipment_values = []

        for item in data:
            # Для обновления резервов
            reserve_values.append((
                item.product_reserves_id,
                item.quantity,
                item.is_fulfilled
            ))

            # Для вставки отгрузок
            shipment_values.append((
                item.author,
                item.supply_id,
                item.product_id,
                item.warehouse_id,
                item.delivery_type,
                item.wb_warehouse,
                item.account,
                item.quantity,
                item.shipment_date,
                False,  # share_of_kit
                None,  # metawild
                item.product_reserves_id
            ))

        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    if shipment_values and reserve_values:
                        # 1. Сначала обновляем резервы
                        await conn.executemany(update_reserve_query, reserve_values)

                        # 2. Затем вставляем записи об отгрузках
                        await conn.executemany(insert_shipment_query, shipment_values)

                    return ShipmentOfGoodsResponse(
                        status=201,
                        message="Успешно обновлены резервы и созданы записи об отгрузке"
                    )

        except asyncpg.PostgresError as e:
            return ShipmentOfGoodsResponse(
                status=422,
                message="PostgresError",
                details=str(e)
            )

    async def creation_reserve_with_movement(self, data: List[CreationWithMovement]) -> ShipmentOfGoodsResponse:
        insert_query = """
        WITH source_reserves AS (
            -- Находим исходные резервы (только существующие)
            SELECT 
                pr.id as source_id,
                pr.ordered as current_ordered,
                mv.quantity_to_move as requested_quantity,
                mv.product_id,
                mv.warehouse_id as target_warehouse_id,
                mv.account,
                mv.delivery_type,
                mv.wb_warehouse,
                mv.reserve_date,
                mv.supply_id as target_supply_id,
                mv.expires_at,
                mv.is_hanging,
                -- Проверяем достаточность количества
                CASE 
                    WHEN pr.ordered >= mv.quantity_to_move THEN mv.quantity_to_move
                    ELSE NULL  -- Если недостаточно - будет ошибка
                END as actual_moved_quantity
            FROM UNNEST(
                $1::varchar[],      -- product_id
                $2::varchar[],      -- move_from_supply  
                $3::integer[],      -- quantity_to_move
                $4::integer[],      -- warehouse_id
                $5::integer[],      -- ordered (из ReserveOfGoodsCreate, но не используется)
                $6::varchar[],      -- account
                $7::varchar[],      -- delivery_type
                $8::varchar[],      -- wb_warehouse
                $9::date[],         -- reserve_date
                $10::varchar[],     -- supply_id (target)
                $11::timestamptz[], -- expires_at
                $12::boolean[]      -- is_hanging
            ) AS mv(
                product_id, move_from_supply, quantity_to_move, warehouse_id, 
                ordered, account, delivery_type, wb_warehouse, reserve_date, 
                supply_id, expires_at, is_hanging
            )
            INNER JOIN product_reserves pr ON pr.product_id = mv.product_id 
                AND pr.supply_id = mv.move_from_supply
                AND pr.ordered >= mv.quantity_to_move  -- Только если хватает количества!
        ),
        updated_sources AS (
            -- Обновляем исходные резервы (вычитаем перемещенное количество)
            UPDATE product_reserves 
            SET ordered = ordered - sr.actual_moved_quantity
            FROM source_reserves sr
            WHERE product_reserves.id = sr.source_id
            RETURNING product_reserves.id as updated_source_id
        ),
        new_reserves AS (
            -- Создаем новые резервы с ссылкой на источник
            INSERT INTO product_reserves (
                product_id, warehouse_id, ordered, account, delivery_type,
                wb_warehouse, reserve_date, supply_id, expires_at, is_fulfilled,
                source_reserve_id, is_hanging
            )
            SELECT 
                sr.product_id,
                sr.target_warehouse_id,
                sr.actual_moved_quantity,  -- Используем перемещенное количество, а не ordered из входных данных
                sr.account,
                sr.delivery_type,
                sr.wb_warehouse,
                sr.reserve_date,
                sr.target_supply_id,
                sr.expires_at,
                false,  -- is_fulfilled всегда false для новых резервов
                sr.source_id,
                sr.is_hanging
            FROM source_reserves sr
            RETURNING id as new_reserve_id, source_reserve_id
        )
        -- Проверяем, что все записи обработаны
        SELECT 
            COUNT(*) as processed_count,
            (SELECT COUNT(*) FROM UNNEST($1::varchar[]) as t) as total_count
        FROM source_reserves;
        """

        # Подготавливаем данные для UNNEST в правильном порядке
        product_ids = [item.product_id for item in data]
        move_from_supplies = [item.move_from_supply for item in data]
        quantities_to_move = [item.quantity_to_move for item in data]
        warehouse_ids = [item.warehouse_id for item in data]
        ordered_values = [item.ordered for item in data]  # Из ReserveOfGoodsCreate, но не используется в логике
        accounts = [item.account for item in data]
        delivery_types = [item.delivery_type for item in data]
        wb_warehouses = [item.wb_warehouse for item in data]
        reserve_dates = [item.reserve_date for item in data]
        supply_ids = [item.supply_id for item in data]  # Целевой supply_id для нового резерва
        expires_ats = [item.expires_at for item in data]
        is_hangings = [item.is_hanging for item in data]

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                result = await conn.fetchrow(
                    insert_query,
                    product_ids,
                    move_from_supplies,
                    quantities_to_move,
                    warehouse_ids,
                    ordered_values,  # ordered из базовой модели
                    accounts,
                    delivery_types,
                    wb_warehouses,
                    reserve_dates,
                    supply_ids,
                    expires_ats,
                    is_hangings
                )

                processed_count = result['processed_count']
                total_count = result['total_count']

                # Если обработано не все - вызываем ошибку (транзакция откатится)
                if processed_count != total_count:
                    # raise Exception(
                    #     f"Не найдены исходные резервы для всех записей или недостаточно количества. "
                    #     f"Обработано: {processed_count}/{total_count}. "
                    #     f"Транзакция откачена."
                    # )
                    return ShipmentOfGoodsResponse(
                        status=404,
                        message="Не найдены исходные резервы для всех записей или недостаточно количества",
                        details=f"Обработано: {processed_count}/{total_count}. Запрос не выполнен"
                    )

                # Возвращаем ID созданных записей
                new_reserves = await conn.fetch("""
                    SELECT id as new_reserve_id, source_reserve_id
                    FROM product_reserves 
                    WHERE source_reserve_id IS NOT NULL
                    ORDER BY id DESC 
                    LIMIT $1
                """, processed_count)

                result = [dict(row) for row in new_reserves]
                return ShipmentOfGoodsResponse(
                    status=201,
                    message="Успешно",
                    details=f"Обработано: {processed_count}/{total_count}. Успешно",
                    data=result
                )

    async def get_summ_reserve_data(self) -> List[SummReserveData]:

        # old
        # query = """
        # SELECT
        #     product_id,
        #     delivery_type,
        #     SUM(ordered - shipped) as current_reserve
        # FROM public.product_reserves
        # GROUP BY product_id, delivery_type
        # ORDER BY product_id, delivery_type;
        # """
        # new
        query = """
                    WITH last_statuses AS (
                SELECT DISTINCT ON (osl.order_id)
                    osl.order_id,
                    osl.status
                FROM public.order_status_log osl
                ORDER BY osl.order_id, osl.created_at DESC
            ),
            valid_tasks AS (
                SELECT 
                    at.task_id,
                    at.article_id,
                    ls.status,
                    EXISTS (
                        SELECT 1 
                        FROM public.historical_statuses_of_assembly_tasks hsat 
                        WHERE hsat.assembly_task_id = at.task_id 
                        AND hsat.wb_status = 'canceled'
                    ) as is_canceled
                FROM public.assembly_task at
                INNER JOIN last_statuses ls ON at.task_id = ls.order_id
                WHERE ls.status IN ('FICTITIOUS_DELIVERED', 'IN_HANGING_SUPPLY', 'IN_TECHNICAL_SUPPLY')
            ),
            fbs_reserves AS (
                SELECT 
                    a.local_vendor_code as product_id,
                    COUNT(*) as current_reserve
                FROM public.article a
                INNER JOIN valid_tasks vt ON a.nm_id = vt.article_id
                WHERE NOT vt.is_canceled
                GROUP BY a.local_vendor_code
                HAVING COUNT(*) > 0
            ),
            fbo_reserves AS (
                SELECT 
                    product_id,
                    SUM(ordered - shipped) as current_reserve
                FROM public.product_reserves
                WHERE delivery_type = 'ФБО'
                GROUP BY product_id
                HAVING SUM(ordered - shipped) > 0
            )
            SELECT 
                product_id,
                'ФБО' as delivery_type,
                current_reserve
            FROM fbo_reserves
            UNION ALL
            SELECT 
                product_id,
                'ФБС' as delivery_type,
                current_reserve
            FROM fbs_reserves
            ORDER BY product_id, delivery_type;
        """
        async with self.pool.acquire() as connection:
            rows = await connection.fetch(query)

            grouped_data = defaultdict(list)

            for row in rows:
                grouped_data[row["product_id"]].append(
                    DeliveryTypeData(
                        reserve_type=row["delivery_type"],
                        current_reserve=int(row["current_reserve"])
                    )
                )

            return [
                SummReserveData(
                    product_id=product_id,
                    delivery_type_data=delivery_type_data
                )
                for product_id, delivery_type_data in grouped_data.items()
            ]

    async def add_shipped_goods_by_id(self, data: List[ShippedGoodsByID]) -> ShipmentOfGoodsResponse:
        pprint(data)
        update_query = """
            UPDATE product_reserves as pr
            SET shipped =  pr.shipped + $2,
            is_fulfilled = $3 
            WHERE id = $1
            RETURNING id, supply_id;
        """

        values = [
            (
                item.reserve_id,
                item.quantity_shipped,
                item.is_fulfilled
            )
            for item in data
        ]
        records = []
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    # Выполняем запрос с возвратом данных
                    for value in values:
                        record = await conn.fetchrow(update_query, *value)
                        records.append(record)

                return ShipmentOfGoodsResponse(
                    status=201,
                    message="Успешно")
        except asyncpg.PostgresError as e:
            return ShipmentOfGoodsResponse(
                status=422,
                message="PostgresError",
                details=str(e)
            )

    async def get_reserved_data(self, is_fulfilled: bool | None, begin_date: datetime.date | None, delivery_type: DeliveryType | None) -> List[ReservedData]:
        query = ("""SELECT 
                    id as reserve_id,
                    product_id,
                    warehouse_id,
                    ordered,
                    shipped,
                    account,
                    delivery_type,
                    supply_id,
                    reserve_date,
                    is_fulfilled,
                    wb_warehouse,
                    expires_at
                  from product_reserves WHERE 1=1""")
        params = []
        param_count = 1

        if is_fulfilled is not None:
            query += f" AND is_fulfilled = ${param_count}"
            params.append(is_fulfilled)
            param_count += 1

        if begin_date is not None:
            print("begin_date", begin_date, type(begin_date))
            query += f" AND reserve_date::date >= ${param_count}::date"
            params.append(begin_date)
            param_count += 1

        if delivery_type is not None:
            query += f" AND  delivery_type = ${param_count}"
            params.append(delivery_type)
            param_count += 1

        print(query)

        async with self.pool.acquire() as conn:
            select_result = await conn.fetch(query, *params)
        return [ReservedData(**res) for res in select_result]

    async def update_data(self, data: List[ShipmentOfGoodsUpdate]):
        data_to_update: List[Tuple] = []
        for shipment_data in data:
            author = shipment_data.author
            supply_id = shipment_data.supply_id
            product_id = shipment_data.product_id
            warehouse_id = shipment_data.warehouse_id
            delivery_type = shipment_data.delivery_type
            wb_warehouse = shipment_data.wb_warehouse
            account = shipment_data.account
            quantity = shipment_data.quantity
            date = shipment_data.shipment_date
            product_reserves_id = shipment_data.product_reserves_id

            tuple_data = (author, supply_id, product_id, warehouse_id, delivery_type, wb_warehouse, account, quantity, date, False, None, product_reserves_id)
            data_to_update.append(tuple_data)
        pprint(data_to_update)
        query_to_insert = """
        INSERT INTO shipment_of_goods (author, supply_id, product_id, warehouse_id, delivery_type,
                               wb_warehouse, account, quantity, shipment_date, share_of_kit, metawild, product_reserves_id)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12);
        """
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    await conn.executemany(query_to_insert, data_to_update)

            result = ShipmentOfGoodsResponse(
                status=201,
                message="Успешно")
        except asyncpg.PostgresError as e:
            result = ShipmentOfGoodsResponse(
                status=422,
                message="PostgresError",
                details=str(e)
            )
        return result

    async def get_shipment_params(self):
        accounts_query = """ SELECT account_name from seller_account;"""
        products_query = """ SELECT id FROM products;"""
        try:
            async with self.pool.acquire() as conn:
                accounts_rows = await conn.fetch(accounts_query)
                accounts = [row['account_name'] for row in accounts_rows]
                products_rows = await conn.fetch(products_query)
                products = [row['id'] for row in products_rows]
                result = ShipmentParamsData(products=products, accounts=accounts)

        except asyncpg.PostgresError as e:
            result = ShipmentOfGoodsResponse(
                status=422,
                message="PostgresError",
                details=str(e)
            )
        return result

    async def create_reserve(self, data: List[ReserveOfGoodsCreate]) -> List[ReserveOfGoodsResponse] | ShipmentOfGoodsResponse:
        insert_query = """
                INSERT INTO product_reserves (
                    product_id,
                    warehouse_id,
                    ordered,
                    account,
                    delivery_type,
                    reserve_date,
                    supply_id,
                    expires_at,                                        
                    wb_warehouse,
                    is_hanging

                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING 
                    id,
                    supply_id
                """

        # Подготавливаем значения для вставки
        values = [
            (
                item.product_id,
                item.warehouse_id,
                item.ordered,
                item.account,
                item.delivery_type,
                item.reserve_date,
                item.supply_id,
                item.expires_at,
                item.wb_warehouse,
                item.is_hanging
            )
            for item in data
        ]
        records = []
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    # Выполняем запрос с возвратом данных
                    for value in values:
                        record = await conn.fetchrow(insert_query, *value)
                        records.append(record)
            # Преобразуем результат в список ReserveOfGoodsResponse
            result = [
                ReserveOfGoodsResponse(
                    product_reserves_id=return_data["id"],
                    supply_id=return_data["supply_id"]  # Добавляем supply_id из связанной транзакции
                )
                for return_data in records
            ]
            print(result)
            return result
        except asyncpg.PostgresError as e:
            result = ShipmentOfGoodsResponse(
                status=422,
                message="PostgresError",
                details=str(e)
            )
            return result

    async def add_shipped_goods(self, data: List[ShippedGoods]) -> List[ReserveOfGoodsResponse] | ShipmentOfGoodsResponse:
        pprint(data)
        update_query = """
            UPDATE product_reserves as pr
            SET shipped =  pr.shipped + $2
            WHERE supply_id = $1 and product_id = $3
            RETURNING id, supply_id;
        """

        values = [
            (
                item.supply_id,
                item.quantity_shipped,
                item.product_id
            )
            for item in data
        ]
        records = []
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    # Выполняем запрос с возвратом данных
                    for value in values:
                        record = await conn.fetchrow(update_query, *value)
                        records.append(record)

            print(records)
            updated_supplies = {r["supply_id"]: r["id"] for r in records if r is not None}

            return [
                ReserveOfGoodsResponse(
                    product_reserves_id=updated_supplies.get(item.supply_id, None),
                    supply_id=item.supply_id
                )
                for item in data
            ]

        except asyncpg.PostgresError as e:
            result = ShipmentOfGoodsResponse(
                status=422,
                message="PostgresError",
                details=str(e)
            )
            return result
