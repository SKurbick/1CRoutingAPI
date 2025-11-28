import json
from datetime import datetime, date, time
from typing import List, Tuple

import asyncpg
from asyncpg import Pool
from app.models import OrderedGoodsFromBuyersUpdate, OrderedGoodsFromBuyersResponse, OrderedGoodsFromBuyersData, PrintedBarcodeData, \
    GoodsAcceptanceCertificateCreate
from app.models.ordered_goods_from_buyers import IsAcceptanceStatus, ReceiptsData


class OrderedGoodsFromBuyersRepository:
    def __init__(self, pool: Pool):
        self.pool = pool

    async def update_data(self, data: List[OrderedGoodsFromBuyersUpdate]):
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    guid_data: list[str] = [doc.guid for doc in data]
                    await conn.execute("""
                    UPDATE ordered_goods_from_buyers
                    SET is_valid = False
                    WHERE guid = ANY($1::varchar[])
                    AND is_valid = True""",
                    guid_data)

                    for doc_data in data:
                        for supply_data in doc_data.supply_data:
                            record_data = (
                                doc_data.guid,
                                doc_data.document_number,
                                doc_data.document_created_at,
                                doc_data.update_document_datetime,
                                doc_data.event_status,
                                doc_data.author_of_the_change,
                                doc_data.our_organizations_name,
                                doc_data.supply_date,
                                supply_data.local_vendor_code,
                                supply_data.quantity,
                                supply_data.amount_with_vat,
                                supply_data.amount_without_vat,
                                doc_data.supplier_name,
                                doc_data.supplier_code,
                                supply_data.product_name,
                                doc_data.expected_receipt_date,
                                doc_data.currency,
                                doc_data.shipment_date,
                                doc_data.payment_document_number,
                                doc_data.payment_indicator,
                                doc_data.receipt_transaction_number,
                                doc_data.comment,
                                supply_data.actual_quantity,
                                supply_data.unit_price,
                                supply_data.last_purchase_supplier,
                                supply_data.last_purchase_price,
                                supply_data.cancelled_due_to
                            )

                            record_id = await conn.fetchval("""
                                    INSERT INTO ordered_goods_from_buyers (guid, document_number, document_created_at, update_document_datetime, event_status,
                           author_of_the_change, our_organizations_name, supply_date, local_vendor_code,
                           quantity, amount_with_vat, amount_without_vat, supplier_name, supplier_code, product_name, warehouse_id,is_valid,
                           expected_receipt_date, currency, shipment_date, payment_document_number, payment_indicator,
                           receipt_transaction_number, comment, actual_quantity, unit_price, last_purchase_supplier,
                           last_purchase_price, cancelled_due_to)
                                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11,  $12, $13, $14, $15, 1, True,
                                            $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27 )
                                    RETURNING id; """, *record_data)

                            for receipt in supply_data.reciepts:
                                await conn.execute("""
                                INSERT INTO receipts_for_ordered_goods_from_buyers (
                                    ordered_goods_from_buyers_id, reciept_number, reciept_date, reciept_quantity, reciept_amount
                                )
                                VALUES ($1, $2, $3, $4, $5);""", record_id, receipt.reciept_number, receipt.reciept_date, receipt.reciept_quantity, receipt.reciept_amount)

                    result = OrderedGoodsFromBuyersResponse(
                        status=201,
                        message="Успешно"
                    )
        except asyncpg.PostgresError as e:
            result = OrderedGoodsFromBuyersResponse(
                status=422,
                message="PostgresError",
                details=str(e)
            )
        return result

    async def get_buyer_orders(self, date_from: date, date_to: date, in_acceptance: bool) -> List[OrderedGoodsFromBuyersData]:
        if in_acceptance:
            query = """
            select
            	ogfb.*,
            	coalesce(
            		json_agg(
            			json_build_object(
            				'reciept_number', rfogfb.reciept_number,
            				'reciept_date', rfogfb.reciept_date,
            				'reciept_quantity', rfogfb.reciept_quantity,
            				'reciept_amount', rfogfb.reciept_amount
            			)
            		) filter (where rfogfb.id is not null), '[]'
            	) as reciepts
            from ordered_goods_from_buyers ogfb 
            left join receipts_for_ordered_goods_from_buyers rfogfb on ogfb.id = rfogfb.ordered_goods_from_buyers_id 
            where
            ogfb.in_acceptance = true and
            ogfb.is_valid = true and
            ogfb.is_printed_barcode = false and 
            ogfb.acceptance_completed = false
            group by 
            ogfb.id;
            """
            async with self.pool.acquire() as conn:
                orders = await conn.fetch(query)

        else:
            datetime_from = datetime.combine(date_from, time.min)  # 2025-04-06 00:00:00
            datetime_to = datetime.combine(date_to, time.max)  # 2025-04-06 23:59:59.999999
            query = """
            select
            	ogfb.*,
            	coalesce(
            		json_agg(
            			json_build_object(
            				'reciept_number', rfogfb.reciept_number,
            				'reciept_date', rfogfb.reciept_date,
            				'reciept_quantity', rfogfb.reciept_quantity,
            				'reciept_amount', rfogfb.reciept_amount
            			)
            		) filter (where rfogfb.id is not null), '[]'
            	) as reciepts
            from ordered_goods_from_buyers ogfb 
            left join receipts_for_ordered_goods_from_buyers rfogfb on ogfb.id = rfogfb.ordered_goods_from_buyers_id 
            where
            ogfb.in_acceptance = false and
            ogfb.is_valid = true and
            ogfb.is_printed_barcode = false and 
            ogfb.acceptance_completed = false and 
            ogfb.supply_date BETWEEN $1 AND $2
            group by 
            ogfb.id;
            """
            async with self.pool.acquire() as conn:
                orders = await conn.fetch(query, datetime_from, datetime_to)

        result = []
        for order in orders:
            order_dict = dict(order)

            receipts_json = order_dict.pop('reciepts', '[]')
            try:
                receipts_list = json.loads(receipts_json) if isinstance(receipts_json, str) else receipts_json
            except json.JSONDecodeError:
                receipts_list = []

            receipts_data = [ReceiptsData(**receipt) for receipt in receipts_list]

            order_data = OrderedGoodsFromBuyersData(
                **order_dict,
                reciepts=receipts_data
            )
            result.append(order_data)

        return result

    async def get_printed_barcodes(self) -> List[PrintedBarcodeData]:
        query = """
                SELECT  gac.*,
                 ogfb.product_name, ogfb.guid, ogfb.document_number, ogfb.document_created_at, ogfb.amount_with_vat, ogfb.amount_without_vat, ogfb.supplier_code,
                  gac.declared_order_quantity , gac.sum_real_quantity,  nb.*  FROM ordered_goods_from_buyers as ogfb 
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
                        "guid": record["guid"],
                        "document_number": record["document_number"],
                        "document_created_at": record["document_created_at"],
                        "amount_with_vat": record["amount_with_vat"],
                        "amount_without_vat": record["amount_without_vat"],
                        "supplier_code": record["supplier_code"],
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
