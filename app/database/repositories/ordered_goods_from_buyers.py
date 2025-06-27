import datetime
from typing import List, Tuple

import asyncpg
from asyncpg import Pool
from app.models import OrderedGoodsFromBuyersUpdate, OrderedGoodsFromBuyersResponse, OrderedGoodsFromBuyersData, PrintedBarcodeData, \
    GoodsAcceptanceCertificateCreate
from app.models.ordered_goods_from_buyers import IsAcceptanceStatus


class OrderedGoodsFromBuyersRepository:
    def __init__(self, pool: Pool):
        self.pool = pool

    async def update_data(self, data: List[OrderedGoodsFromBuyersUpdate]):
        data_to_update: List[Tuple] = []
        guid_data: List[str] = []
        for document_data in data:
            guid = document_data.guid
            document_number = document_data.document_number
            document_created_at = document_data.document_created_at
            update_document_datetime = document_data.update_document_datetime
            event_status = document_data.event_status
            author_of_the_change = document_data.author_of_the_change
            our_organizations_name = document_data.our_organizations_name
            supply_date = document_data.supply_date
            supplier_name = document_data.supplier_name
            supplier_code = document_data.supplier_code
            guid_data.append(guid)
            for supply_data in document_data.supply_data:
                local_vendor_code = supply_data.local_vendor_code
                quantity = supply_data.quantity
                amount_with_vat = supply_data.amount_with_vat
                amount_without_vat = supply_data.amount_without_vat
                product_name = supply_data.product_name
                data_to_update.append((guid, document_number, document_created_at, update_document_datetime, event_status,
                                       author_of_the_change, our_organizations_name, supply_date, local_vendor_code,
                                       quantity, amount_with_vat, amount_without_vat, supplier_name, supplier_code, product_name))

        query_update_is_valid = """
        UPDATE ordered_goods_from_buyers
        SET is_valid = False
        WHERE guid = ANY($1::varchar[])
        AND is_valid = True
        """
        query_to_insert = """
        INSERT INTO ordered_goods_from_buyers (guid, document_number, document_created_at, update_document_datetime, event_status,
                               author_of_the_change, our_organizations_name, supply_date, local_vendor_code,
                               quantity, amount_with_vat, amount_without_vat, supplier_name, supplier_code, product_name, warehouse_id,is_valid)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11,  $12, $13, $14, $15, 1, True); """  # по умолчанию передаём основной склад

        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    await conn.execute(query_update_is_valid, guid_data)
                    await conn.executemany(query_to_insert, data_to_update)
                result = OrderedGoodsFromBuyersResponse(
                    status=201,
                    message="Успешно")
        except asyncpg.PostgresError as e:
            result = OrderedGoodsFromBuyersResponse(
                status=422,
                message="PostgresError",
                details=str(e)
            )
        return result

    async def get_buyer_orders(self, date_from: datetime.date, date_to: datetime.date, in_acceptance: bool) -> List[OrderedGoodsFromBuyersData]:
        if in_acceptance:
            query = """
            SELECT * FROM ordered_goods_from_buyers
            WHERE 
                in_acceptance = TRUE and is_valid = TRUE and is_printed_barcode = FALSE and acceptance_completed = FALSE;
            """
            async with self.pool.acquire() as conn:
                records = await conn.fetch(query)

        else:
            datetime_from = datetime.datetime.combine(date_from, datetime.time.min)  # 2025-04-06 00:00:00
            datetime_to = datetime.datetime.combine(date_to, datetime.time.max)  # 2025-04-06 23:59:59.999999
            query = """
            SELECT * FROM ordered_goods_from_buyers
            WHERE
                in_acceptance = FALSE AND is_valid = TRUE AND is_printed_barcode = FALSE AND acceptance_completed = FALSE AND
                supply_date BETWEEN $1 AND $2;
            """
            async with self.pool.acquire() as conn:
                records = await conn.fetch(query, datetime_from, datetime_to)

        # Преобразуем записи в Pydantic модели
        return [OrderedGoodsFromBuyersData(**record) for record in records]

    async def get_printed_barcodes(self) -> List[PrintedBarcodeData]:
            query = """
                SELECT  gac.*, ogfb.product_name , gac.declared_order_quantity , gac.sum_real_quantity,  nb.*  FROM ordered_goods_from_buyers as ogfb 
                join goods_acceptance_certificate as gac on ogfb.id = gac.ordered_goods_from_buyers_id 
                join nested_box nb on nb.goods_acceptance_certificate_id = gac.id
                WHERE 
                ogfb.in_acceptance = TRUE and ogfb.is_valid = TRUE and ogfb.is_printed_barcode = TRUE and ogfb.acceptance_completed = FALSE;
            """
            async with self.pool.acquire() as conn:
                records = await conn.fetch(query)

                certs = {}
                for record in records:
                    cert_id = record['ordered_goods_from_buyers_id']
                    if cert_id not in certs:
                        certs[cert_id] = {
                            "ordered_goods_from_buyers_id": record["ordered_goods_from_buyers_id"],
                            "product": record["product"],
                            "product_name": record["product_name"],
                            "declared_order_quantity": int(record["declared_order_quantity"]),
                            "sum_real_quantity": int(record["sum_real_quantity"]),
                            "acceptance_author": record["acceptance_author"],
                            "warehouse_id": record["warehouse_id"],
                            "added_photo_link": record["added_photo_link"],  # photo_link на верхнем уровне
                            "nested_box_data": []
                        }

                    certs[cert_id]["nested_box_data"].append({
                        "quantity_of_boxes": int(record["quantity_of_boxes"]),
                        "quantity_in_a_box": int(record["quantity_in_a_box"]),
                        "is_box": record["is_box"]
                        # photo_link НЕ добавляем сюда
                    })

                return [PrintedBarcodeData(**cert) for cert in certs.values()]


    async def get_photo_link_by_wilds(self, vendor_codes: List[str]):

        query = """
            SELECT DISTINCT ON (a.local_vendor_code) 
                a.local_vendor_code, 
                cd.photo_link 
            FROM article AS a
            JOIN card_data cd ON a.nm_id = cd.article_id
            WHERE a.account = 'ВЕКТОР' 
            AND a.local_vendor_code = ANY($1::text[])
            ORDER BY a.local_vendor_code;
        """
        async with self.pool.acquire() as conn:
            result = await conn.fetch(query, vendor_codes)

        return {res['local_vendor_code']: res['photo_link'] for res in result}

    async def update_acceptance_status(self, data: List[IsAcceptanceStatus]):
        data_to_update = [(value.id, value.in_acceptance) for value in data]
        print(data)
        query_update_is_acceptance = """
            UPDATE ordered_goods_from_buyers
            SET in_acceptance = $2
            WHERE id = $1;
        """

        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    await conn.executemany(query_update_is_acceptance, data_to_update)
                result = OrderedGoodsFromBuyersResponse(
                    status=201,
                    message="Успешно")
        except asyncpg.PostgresError as e:
            result = OrderedGoodsFromBuyersResponse(
                status=422,
                message="PostgresError",
                details=str(e)
            )
        return result
