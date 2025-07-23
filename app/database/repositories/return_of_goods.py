import json
from collections import defaultdict
from pprint import pprint
from typing import List, Tuple

import asyncpg
from asyncpg import Pool
from app.models.return_of_goods import ReturnOfGoodsResponse, ReturnOfGoodsData, GoodsReturn, IncomingReturns


class ReturnOfGoodsRepository:
    def __init__(self, pool: Pool):
        self.pool = pool

    async def get_return_of_goods(self) -> List[ReturnOfGoodsData] | ReturnOfGoodsResponse:
        select_query = """
            SELECT 
                COALESCE(a.local_vendor_code, 'не найден артикул продавца по артикулу wb') AS product_id,
                gr.*
            FROM 
                public.goods_returns gr
            LEFT JOIN 
                public.article a ON gr.nm_id = a.nm_id
            WHERE 
                gr.status = 'Выдано' AND gr.is_received = false
            ORDER BY 
                a.local_vendor_code;
        """
        try:
            async with self.pool.acquire() as conn:
                query_result = await conn.fetch(select_query)

                grouped_data = defaultdict(list)
                for row in query_result:
                    row_dict = dict(row)
                    product_id = row_dict.pop("product_id")  # Извлекаем local_vendor_code
                    grouped_data[product_id].append(GoodsReturn(**row_dict))

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

    async def incoming_returns(self, data: List[IncomingReturns]) -> ReturnOfGoodsResponse:
        # get_wilds_in_products = """SELECT id, kit_components FROM products WHERE is_kit=TRUE;"""
        # async with self.pool.acquire() as conn:
        #     products_data = await conn.fetch(get_wilds_in_products)
        #     meta_wilds = {record['id']: record['kit_components'] for record in products_data}  # получаем все валидные id товаров
        #     pprint(meta_wilds)
        data_to_add_incoming_returns: List[Tuple] = []
        data_to_update_goods_returns: List[Tuple] = []
        for return_data in data:
            product_id = return_data.product_id
            quantity = return_data.sum_quantity
            author = return_data.author
            warehouse_id = return_data.warehouse_id
            return_date = return_data.return_date
            for is_received_data in return_data.is_received_data:
                data_to_update_goods_returns.append((is_received_data.id, is_received_data.is_received))
            # if product_id in meta_wilds:
            #     kit_components = json.loads(meta_wilds[product_id])
            #     print(type(kit_components))
            #     print(kit_components)
            #     for wild, qty in kit_components.items():
            #         data_to_add_incoming_returns.append(
            #             (author, wild, warehouse_id, quantity, return_date, True, product_id)
            #         )
            #     continue
            tuple_data = (author, product_id, warehouse_id, quantity, return_date, False, None)
            data_to_add_incoming_returns.append(tuple_data)
        query_to_insert_incoming_returns = """
        INSERT INTO incoming_returns (author, product_id, warehouse_id, quantity, return_date, share_of_kit, metawild)
        VALUES ($1, $2, $3, $4, $5, $6, $7);
        """
        query_update_is_received = """
            UPDATE goods_returns
            SET is_received = $2
            WHERE id = $1;
        """
        try:
            async with self.pool.acquire() as conn:
                pprint(data_to_add_incoming_returns)
                async with conn.transaction():
                    await conn.executemany(query_to_insert_incoming_returns, data_to_add_incoming_returns)
                    await conn.executemany(query_update_is_received, data_to_update_goods_returns)
            result = ReturnOfGoodsResponse(
                status=201,
                message="Успешно")
        except asyncpg.PostgresError as e:
            result = ReturnOfGoodsResponse(
                status=422,
                message="PostgresError",
                details=str(e)
            )
        return result
