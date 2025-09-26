import json
from collections import defaultdict
from pprint import pprint
from typing import List, Tuple

import asyncpg
from asyncpg import Pool
from app.models.return_of_goods import ReturnOfGoodsResponse, ReturnOfGoodsData, GoodsReturn, IncomingReturns, GroupDataGoodsReturns, ReturnsOneCModelAdd, \
    OneCReturnDataByProduct


class ReturnOfGoodsRepository:
    def __init__(self, pool: Pool):
        self.pool = pool

    async def get_incoming_data_for_one_c(self, data:List[IncomingReturns]) -> List[ReturnsOneCModelAdd]:

        srids: List[str] = []
        return_date = None
        author = None
        for values in data:
            return_date = str(values.return_date)
            author = values.author
            for is_received_data in values.is_received_data:
                srids.append(is_received_data.srid)

        select_query = """
            SELECT 
                sa.inn,
                p."name",
                COALESCE(a.local_vendor_code, 'не найден артикул продавца по артикулу wb') AS product_id,
                grd.account,
                COUNT(*) AS total_quantity
            FROM goods_returns_dev grd 
            JOIN seller_account sa ON UPPER(grd.account) = UPPER(sa.account_name)
            JOIN article a ON grd.nm_id = a.nm_id
            JOIN products p ON p.id = a.local_vendor_code
           WHERE grd.srid = ANY($1::text[])
         GROUP BY 
                sa.inn,
                product_id,
                grd.account,
                 p."name"
            ORDER BY sa.inn,
            grd.account,
            p."name",
            product_id;
        """


        async with self.pool.acquire() as conn:
            records = await conn.fetch(select_query, srids)


        # Группируем по (account, inn)
        grouped = {}
        for row in records:
            key = (row['account'], row['inn'])
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(
                OneCReturnDataByProduct(
                    product_id=row['product_id'],
                    product_name=row['name'],  # заглушка, т.к. нет в SQL
                    quantity=row['total_quantity']
                )
            )

        # Формируем результат
        result = []
        for (account, inn), products in grouped.items():
            result.append(
                ReturnsOneCModelAdd(
                    account=account,
                    author=author,
                    inn=str(inn),
                    return_date=return_date,
                    return_data_by_product=products
                )
            )

        return result

    async def get_return_of_goods(self) -> List[ReturnOfGoodsData] | ReturnOfGoodsResponse:
        select_query = """
                SELECT 
                    -- Артикул продавца (или заглушка, если не найден)
                    COALESCE(a.local_vendor_code, 'не найден артикул продавца по артикулу wb') AS product_id,
                    -- Поля из goods_returns_dev
                    grd.srid,
                    grd.account,
                    grd.barcode,
                    grd.brand,
                    grd.dst_office_address,
                    grd.dst_office_id,
                    grd.nm_id,
                    grd.order_dt,
                    grd.order_id,
                    grd.return_type,
                    grd.shk_id,
                    grd.sticker_id,
                    grd.subject_name,
                    grd.tech_size,
                    grd.reason,
                    grd.is_status_active,
                    grd.created_at AS goods_created_at,
                    grd.is_received,
                    -- Поля из goods_returns_status_history
                    grsh.status,
                    grsh.status_dt,
                    grsh.completed_dt,
                    grsh.expired_dt,
                    grsh.ready_to_return_dt,
                    grsh.created_at AS status_created_at
                FROM 
                    public.goods_returns_dev grd
                    LEFT JOIN public.article a ON grd.nm_id = a.nm_id
                    JOIN (
                        -- Подзапрос: берём только последнюю запись статуса по времени для каждого srid
                        SELECT 
                            *,
                            ROW_NUMBER() OVER (PARTITION BY srid ORDER BY created_at DESC) AS rn
                        FROM 
                            public.goods_returns_status_history
                    ) grsh ON grd.srid = grsh.srid AND grsh.rn = 1
                WHERE 
                    grd.is_received = FALSE
                ORDER BY 
                    a.local_vendor_code;
        """
        #                    grsh.status IN ('Выдано', 'Готов к выдаче') AND
        try:
            async with self.pool.acquire() as conn:
                query_result = await conn.fetch(select_query)

                grouped_data = defaultdict(list)
                for row in query_result:
                    row_dict = dict(row)
                    product_id = row_dict.pop("product_id")  # Извлекаем local_vendor_code
                    grouped_data[product_id].append(GroupDataGoodsReturns(**row_dict))

                result = [
                    # Преобразуем в список ReturnOfGoodsData
                    ReturnOfGoodsData(product_id=product_id, group_data=items)
                    for product_id, items in grouped_data.items()
                ]
                pprint(result)
                return result

        except asyncpg.PostgresError as e:
            return ReturnOfGoodsResponse(
                status=422,
                message="PostgresError",
                details=str(e)
            )

    # async def incoming_returns(self, data: List[IncomingReturns]) -> ReturnOfGoodsResponse:
    #
    #     data_to_add_incoming_returns: List[Tuple] = []
    #     data_to_update_goods_returns: List[Tuple] = []
    #     for return_data in data:
    #         product_id = return_data.product_id
    #         quantity = return_data.sum_quantity
    #         author = return_data.author
    #         warehouse_id = return_data.warehouse_id
    #         return_date = return_data.return_date
    #         for is_received_data in return_data.is_received_data:
    #             data_to_update_goods_returns.append((is_received_data.srid, is_received_data.is_received))
    #
    #         tuple_data = (author, product_id, warehouse_id, quantity, return_date, False, None)
    #         data_to_add_incoming_returns.append(tuple_data)
    #     query_to_insert_incoming_returns = """
    #     INSERT INTO incoming_returns (author, product_id, warehouse_id, quantity, return_date, share_of_kit, metawild)
    #     VALUES ($1, $2, $3, $4, $5, $6, $7);
    #     """
    #     query_update_is_received = """
    #         UPDATE goods_returns_dev
    #         SET is_received = $2
    #         WHERE srid = $1;
    #     """
    #     try:
    #         async with self.pool.acquire() as conn:
    #             pprint(data_to_add_incoming_returns)
    #             async with conn.transaction():
    #                 await conn.executemany(query_to_insert_incoming_returns, data_to_add_incoming_returns)
    #                 await conn.executemany(query_update_is_received, data_to_update_goods_returns)
    #         result = ReturnOfGoodsResponse(
    #             status=201,
    #             message="Успешно")
    #     except asyncpg.PostgresError as e:
    #         result = ReturnOfGoodsResponse(
    #             status=422,
    #             message="PostgresError",
    #             details=str(e)
    #         )
    #     return result

    async def incoming_returns(self, data: List[IncomingReturns]) -> ReturnOfGoodsResponse:
        data_to_add_incoming_returns: List[Tuple] = []
        goods_returns_update_data: List[Tuple] = []

        # Подготовка данных для вставки в incoming_returns
        for return_data in data:
            tuple_data = (
                return_data.author,
                return_data.product_id,
                return_data.warehouse_id,
                return_data.sum_quantity,
                return_data.return_date,
                False,
                None
            )
            data_to_add_incoming_returns.append(tuple_data)

        query_to_insert_incoming_returns = """
        INSERT INTO incoming_returns (author, product_id, warehouse_id, quantity, return_date, share_of_kit, metawild)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING id;
        """

        query_update_goods_returns = """
        UPDATE goods_returns_dev 
        SET is_received = $2, incoming_return_id = $3
        WHERE srid = $1;
        """

        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    # Вставляем записи и получаем их ID
                    inserted_ids = []
                    for insert_data in data_to_add_incoming_returns:
                        row = await conn.fetchrow(query_to_insert_incoming_returns, *insert_data)
                        inserted_ids.append(row['id'])

                    # Подготавливаем данные для обновления goods_returns_dev
                    update_data = []
                    for i, return_data in enumerate(data):
                        incoming_return_id = inserted_ids[i]  # ID только что вставленной записи
                        for is_received_data in return_data.is_received_data:
                            update_data.append((
                                is_received_data.srid,
                                is_received_data.is_received,
                                incoming_return_id  # Добавляем связь
                            ))

                    # Обновляем goods_returns_dev
                    await conn.executemany(query_update_goods_returns, update_data)

            result = ReturnOfGoodsResponse(
                status=201,
                message="Успешно"
            )
        except asyncpg.PostgresError as e:
            result = ReturnOfGoodsResponse(
                status=422,
                message="PostgresError",
                details=str(e)
            )
        return result