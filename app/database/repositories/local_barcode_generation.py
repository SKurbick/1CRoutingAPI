from pprint import pprint
from typing import List, Tuple

from asyncpg import Pool
from app.models import GoodsAcceptanceCertificateCreate


class LocalBarcodeGenerationRepository:
    def __init__(self, pool: Pool):
        self.pool = pool

    async def create_data(self, data: GoodsAcceptanceCertificateCreate):

        goods_acceptance_certificate_query = """
        INSERT INTO goods_acceptance_certificate (
                            ordered_goods_from_buyers_id,
                            product,
                            declared_order_quantity,
                            sum_real_quantity,
                            acceptance_author,
                            warehouse_id,
                             photo_link)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING *
        """
        nested_box_query = """
                INSERT INTO nested_box (
                    product,
                    quantity_of_boxes,
                    quantity_in_a_box,
                    is_box,
                    goods_acceptance_certificate_id )
                    VALUES ($1, $2, $3, $4, $5)
                    RETURNING *
        """
        data_to_add_barcodes: List[Tuple] = []
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                gac_inserted_row = await conn.fetchrow(
                    goods_acceptance_certificate_query,
                    data.ordered_goods_from_buyers_id, data.product,
                    data.declared_order_quantity, data.sum_real_quantity,
                    data.acceptance_author, data.warehouse_id, data.photo_link
                )
                for nested_box in data.nested_box_data:
                    nb_insert_row = await conn.fetchrow(
                        nested_box_query,
                        data.product, nested_box.quantity_of_boxes,
                        nested_box.quantity_in_a_box, nested_box.is_box, gac_inserted_row['id']
                    )
                    if nested_box.is_box:
                        for i in range(nested_box.quantity_of_boxes):
                            data_to_add_barcodes.append(
                                (data.product, data.product_name, nested_box.quantity_in_a_box, nested_box.quantity_in_a_box, nested_box.is_box, gac_inserted_row['id'],
                                 data.ordered_goods_from_buyers_id)
                            )

                data = await self.add_barcode_data(conn, data_to_add_barcodes)
                pprint(data)
        return data

    async def add_barcode_data(self, conn, data_to_add_barcodes:List[Tuple]):
        create_temp_table_query = """
                CREATE TEMP TABLE temp_barcode_data (
            LIKE local_barcode_data INCLUDING DEFAULTS
            EXCLUDING INDEXES EXCLUDING CONSTRAINTS
        ) ON COMMIT DROP;
        """
        disable_trigger_query = """ALTER TABLE temp_barcode_data DISABLE TRIGGER ALL;"""
        executemany_in_temp_table_query ="""
        INSERT INTO temp_barcode_data (
            product,
            product_name,
            beginning_quantity,
            balance,
            is_box,
            goods_acceptance_certificate_id,
            ordered_goods_from_buyers_id
        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        """
        moved_in_base_table_and_return_query = """
        WITH moved AS (
            INSERT INTO local_barcode_data
            SELECT * FROM temp_barcode_data
            RETURNING 
                id,
                local_barcode,
                product,
                product_name,
                beginning_quantity,
                goods_acceptance_certificate_id
        )
        SELECT * FROM moved ORDER BY id;
        """
        await conn.execute(create_temp_table_query)

        # 2. Отключаем триггеры для временной таблицы (опционально)
        await conn.execute(disable_trigger_query)

        # 3. Быстрая вставка во временную таблицу
        await conn.executemany(executemany_in_temp_table_query, data_to_add_barcodes)

        # 4. Перенос в основную таблицу с RETURNING
        inserted_records = await conn.fetch(moved_in_base_table_and_return_query)

        return [dict(record) for record in inserted_records]
