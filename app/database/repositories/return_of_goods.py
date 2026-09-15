import json
import datetime
from collections import defaultdict
from typing import List, Tuple

import asyncpg
from asyncpg import Pool
from app.models.return_of_goods import ReturnOfGoodsResponse, ReturnOfGoodsData, GoodsReturn, IncomingReturns, GroupDataGoodsReturns, ReturnsOneCModelAdd, \
    ManualUnidentifiedReturn, OneCReturnDataByProduct, UnidentifiedGoodsReturn


class ReturnOfGoodsRepository:
    def __init__(self, pool: Pool):
        self.pool = pool

    async def get_incoming_data_for_one_c(self, data:List[IncomingReturns]) -> List[ReturnsOneCModelAdd]:

        srids: List[str] = []
        return_date = None
        author = None
        mark_list_by_product = defaultdict(list)
        for values in data:
            return_date = str(values.return_date)
            author = values.author
            if values.mark_list:
                mark_list_by_product[values.product_id].extend(values.mark_list)
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
                    quantity=row['total_quantity'],
                    mark_list=mark_list_by_product.get(row['product_id']) or None
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

    async def get_return_of_goods(
            self,
            date_from: datetime.date | None = None,
    ) -> List[ReturnOfGoodsData] | ReturnOfGoodsResponse:
        select_query = """
                WITH filtered_returns AS MATERIALIZED (
                    SELECT *
                    FROM public.goods_returns_dev
                    WHERE is_received = FALSE
                        AND ($1::date IS NULL OR created_at >= $1::date)
                ),
                latest_status AS MATERIALIZED (
                    SELECT DISTINCT ON (srid)
                        srid,
                        status,
                        status_dt,
                        completed_dt,
                        expired_dt,
                        ready_to_return_dt,
                        created_at
                    FROM public.goods_returns_status_history
                    ORDER BY srid, created_at DESC
                )
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
                    filtered_returns grd
                    LEFT JOIN public.article a ON grd.nm_id = a.nm_id
                    JOIN latest_status grsh ON grd.srid = grsh.srid
                ORDER BY 
                    a.local_vendor_code;
        """
        #                    grsh.status IN ('Выдано', 'Готов к выдаче') AND
        try:
            async with self.pool.acquire() as conn:
                query_result = await conn.fetch(select_query, date_from)

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
                return result

        except asyncpg.PostgresError as e:
            return ReturnOfGoodsResponse(
                status=422,
                message="PostgresError",
                details=str(e)
            )

    async def get_unidentified_goods(
            self,
            date_from: datetime.date | None = None,
    ) -> List[UnidentifiedGoodsReturn] | ReturnOfGoodsResponse:
        select_query = """
                WITH latest_status AS MATERIALIZED (
                    SELECT DISTINCT ON (srid)
                        srid,
                        status,
                        status_dt,
                        completed_dt,
                        expired_dt,
                        ready_to_return_dt,
                        created_at
                    FROM public.goods_returns_status_history
                    ORDER BY srid, created_at DESC
                )
                SELECT
                    'не найден артикул продавца по артикулу wb' AS product_id,
                    CASE
                        WHEN a.nm_id IS NULL THEN 'nm_id отсутствует в таблице article'
                        ELSE 'для nm_id не заполнен local_vendor_code в таблице article'
                    END AS identification_error,
                    (grsh.srid IS NOT NULL) AS status_history_found,
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
                    grsh.status,
                    grsh.status_dt,
                    grsh.completed_dt,
                    grsh.expired_dt,
                    grsh.ready_to_return_dt,
                    grsh.created_at AS status_created_at
                FROM public.goods_returns_dev grd
                LEFT JOIN public.article a ON grd.nm_id = a.nm_id
                LEFT JOIN latest_status grsh ON grd.srid = grsh.srid
                WHERE a.local_vendor_code IS NULL
                    AND ($1::date IS NULL OR grd.created_at >= $1::date)
                ORDER BY grd.created_at DESC;
        """
        try:
            async with self.pool.acquire() as conn:
                query_result = await conn.fetch(select_query, date_from)
            return [UnidentifiedGoodsReturn(**dict(row)) for row in query_result]
        except asyncpg.PostgresError as e:
            return ReturnOfGoodsResponse(
                status=422,
                message="PostgresError",
                details=str(e),
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

    async def receive_unidentified(
            self,
            data: ManualUnidentifiedReturn,
    ) -> ReturnOfGoodsResponse:
        lock_query = """
            SELECT
                grd.srid,
                grd.nm_id,
                grd.account,
                grd.is_received,
                grd.incoming_return_id,
                a.local_vendor_code
            FROM public.goods_returns_dev grd
            LEFT JOIN public.article a ON a.nm_id = grd.nm_id
            WHERE grd.srid = ANY($1::text[])
            FOR UPDATE OF grd;
        """
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    product_exists = await conn.fetchval(
                        "SELECT EXISTS(SELECT 1 FROM public.products WHERE id = $1)",
                        data.product_id,
                    )
                    if not product_exists:
                        return ReturnOfGoodsResponse(
                            status=422,
                            message="Товар не найден",
                            details=f"product_id={data.product_id} отсутствует в products",
                        )

                    warehouse_exists = await conn.fetchval(
                        "SELECT EXISTS(SELECT 1 FROM public.warehouses WHERE id = $1)",
                        data.warehouse_id,
                    )
                    if not warehouse_exists:
                        return ReturnOfGoodsResponse(
                            status=422,
                            message="Склад не найден",
                            details=f"warehouse_id={data.warehouse_id} отсутствует в warehouses",
                        )

                    records = await conn.fetch(lock_query, data.srids)
                    records_by_srid = {row["srid"]: row for row in records}
                    missing_srids = [srid for srid in data.srids if srid not in records_by_srid]
                    if missing_srids:
                        return ReturnOfGoodsResponse(
                            status=422,
                            message="Возвраты не найдены",
                            details=", ".join(missing_srids),
                        )

                    already_received = [
                        row["srid"] for row in records
                        if row["is_received"] is True or row["incoming_return_id"] is not None
                    ]
                    if already_received:
                        return ReturnOfGoodsResponse(
                            status=409,
                            message="Часть возвратов уже оприходована",
                            details=", ".join(already_received),
                        )

                    identified_srids = [
                        row["srid"] for row in records
                        if row["local_vendor_code"] is not None
                    ]
                    if identified_srids:
                        return ReturnOfGoodsResponse(
                            status=422,
                            message="Метод предназначен только для неопознанных товаров",
                            details=", ".join(identified_srids),
                        )

                    accounts = {row["account"] for row in records}
                    if len(accounts) != 1 or None in accounts:
                        return ReturnOfGoodsResponse(
                            status=422,
                            message="Возвраты должны относиться к одному аккаунту",
                            details="Передайте отдельный запрос для каждого account",
                        )
                    account = next(iter(accounts))
                    seller_account_exists = await conn.fetchval(
                        "SELECT EXISTS(SELECT 1 FROM public.seller_account WHERE UPPER(account_name) = UPPER($1))",
                        account,
                    )
                    if not seller_account_exists:
                        return ReturnOfGoodsResponse(
                            status=422,
                            message="Аккаунт продавца не найден",
                            details=f"account={account} отсутствует в seller_account",
                        )

                    incoming_return_id = await conn.fetchval(
                        """
                        INSERT INTO public.incoming_returns
                            (author, product_id, warehouse_id, quantity, return_date, share_of_kit, metawild)
                        VALUES ($1, $2, $3, $4, $5, FALSE, NULL)
                        RETURNING id;
                        """,
                        data.author,
                        data.product_id,
                        data.warehouse_id,
                        len(data.srids),
                        data.return_date,
                    )

                    await conn.execute(
                        """
                        UPDATE public.goods_returns_dev
                        SET is_received = TRUE, incoming_return_id = $2
                        WHERE srid = ANY($1::text[]);
                        """,
                        data.srids,
                        incoming_return_id,
                    )

                    audit_data = []
                    for row in records:
                        comment = data.comment or (
                            f"Ручная идентификация: nm_id={row['nm_id']}; "
                            f"назначен product_id={data.product_id}."
                        )
                        audit_data.append((
                            row["srid"],
                            data.product_id,
                            row["nm_id"],
                            data.author,
                            comment,
                            incoming_return_id,
                        ))
                    await conn.executemany(
                        """
                        INSERT INTO public.goods_return_manual_identifications
                            (srid, product_id, original_nm_id, resolved_by, comment, incoming_return_id)
                        VALUES ($1, $2, $3, $4, $5, $6);
                        """,
                        audit_data,
                    )

                    if data.mark_list:
                        await conn.executemany(
                            """
                            INSERT INTO public.goods_returns_mark_list (mark_code, author, product_id)
                            VALUES ($1, $2, $3);
                            """,
                            [
                                (mark.mark_code, data.author, data.product_id)
                                for mark in data.mark_list
                            ],
                        )

            return ReturnOfGoodsResponse(status=201, message="Успешно")
        except asyncpg.PostgresError as e:
            return ReturnOfGoodsResponse(
                status=422,
                message="PostgresError",
                details=str(e),
            )

    async def get_manual_incoming_data_for_one_c(
            self,
            data: ManualUnidentifiedReturn,
    ) -> List[ReturnsOneCModelAdd]:
        query = """
            SELECT
                grd.account,
                sa.inn,
                p.name AS product_name,
                COUNT(*) AS quantity
            FROM public.goods_returns_dev grd
            JOIN public.seller_account sa
                ON UPPER(grd.account) = UPPER(sa.account_name)
            JOIN public.products p ON p.id = $2
            WHERE grd.srid = ANY($1::text[])
            GROUP BY grd.account, sa.inn, p.name;
        """
        async with self.pool.acquire() as conn:
            records = await conn.fetch(query, data.srids, data.product_id)
        return [
            ReturnsOneCModelAdd(
                account=row["account"],
                author=data.author,
                inn=str(row["inn"]),
                return_date=str(data.return_date),
                return_data_by_product=[
                    OneCReturnDataByProduct(
                        product_id=data.product_id,
                        product_name=row["product_name"],
                        quantity=row["quantity"],
                        mark_list=data.mark_list,
                    )
                ],
            )
            for row in records
        ]

    async def incoming_returns(self, data: List[IncomingReturns]) -> ReturnOfGoodsResponse:
        data_to_add_incoming_returns: List[Tuple] = []
        data_to_insert_goods_returns_mark_list: List[Tuple] = []

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

            if return_data.mark_list:
                for mark_data in return_data.mark_list:
                    data_to_insert_goods_returns_mark_list.append((
                        mark_data.mark_code,
                        return_data.author,
                        return_data.product_id
                    ))

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

        query_to_insert_goods_returns_mark_list = """
        INSERT INTO goods_returns_mark_list (mark_code, author, product_id)
        VALUES ($1, $2, $3);
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

                    if data_to_insert_goods_returns_mark_list:
                        await conn.executemany(
                            query_to_insert_goods_returns_mark_list,
                            data_to_insert_goods_returns_mark_list
                        )

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