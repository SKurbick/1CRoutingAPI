"""
WMS Integration Service
Обработка поступлений из 1С и создание movements в WMS
"""

import logging
import json
import os
from logging.handlers import RotatingFileHandler
from typing import List, Dict, Any, Set
import httpx
from app.dependencies.config import settings

# ============================================================================
# Настройка логирования в файл
# ============================================================================
logger = logging.getLogger(__name__)

_log_dir = '/app/logs' if os.path.exists('/app') else os.path.join(os.path.dirname(os.path.abspath(__file__)), '../logs')
os.makedirs(os.path.normpath(_log_dir), exist_ok=True)
_log_path = os.path.normpath(os.path.join(_log_dir, 'wms_integration.log'))

file_handler = RotatingFileHandler(
    _log_path,
    maxBytes=10 * 1024 * 1024,  # 10 MB
    backupCount=5,
    encoding='utf-8'
)
file_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter(
    '%(asctime)s | %(levelname)s | %(funcName)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.setLevel(logging.DEBUG)


class WMSIntegrationService:
    """Сервис интеграции с WMS для обработки поступлений"""

    # Константы (можно вынести в .env если нужно)
    RECEIPT_LOCATION = "PUSHKINO-ПРИЁМКА"
    EXCLUDED_SUPPLIER_CODE = "9714053621"  # ВБ (исключаем)

    def __init__(self, receipt_repository, pool):
        """
        Args:
            receipt_repository: WMSReceiptRepository для работы с поступлениями
            pool: asyncpg pool для запросов к БД
        """
        self.receipt_repo = receipt_repository
        self.pool = pool

    async def process_receipts(self, receipts: List[Any]) -> Dict[str, Any]:
        """
        Обработать список поступлений из 1С

        Args:
            receipts: Список ReceiptOfGoodsUpdate

        Returns:
            Статистика обработки
        """
        # ============================================================================
        # ЛОГИРОВАНИЕ: Начало обработки
        # ============================================================================
        logger.info("=" * 80)
        logger.info(f"WMS Integration START | Получено поступлений: {len(receipts)}")
        logger.debug(f"Receipts data: {json.dumps([r.model_dump() for r in receipts], ensure_ascii=False, default=str)}")

        stats = {
            "processed_receipts": 0,
            "created_movements": 0,
            "adjusted_movements": 0,
            "skipped_products": [],
            "adjustment_warnings": [],
            "errors": []
        }

        # Получить список валидных товаров
        valid_products = await self._get_valid_products()
        logger.info(f"Valid products count: {len(valid_products)}")
        logger.debug(f"Valid products (first 20): {list(valid_products)[:20]}...")

        for receipt in receipts:
            try:
                await self._process_single_receipt(
                    receipt=receipt,
                    valid_products=valid_products,
                    stats=stats
                )
                stats["processed_receipts"] += 1
            except Exception as e:
                logger.error(f"Error processing receipt {receipt.guid}: {e}")
                stats["errors"].append({
                    "guid": receipt.guid,
                    "error": str(e)
                })

        # ============================================================================
        # ЛОГИРОВАНИЕ: Завершение обработки
        # ============================================================================
        logger.info("=" * 80)
        logger.info(f"WMS Integration COMPLETE")
        logger.info(f"  Processed receipts: {stats['processed_receipts']}")
        logger.info(f"  Created movements: {stats['created_movements']}")
        logger.info(f"  Adjusted movements: {stats['adjusted_movements']}")
        logger.info(f"  Skipped products: {len(stats['skipped_products'])}")
        logger.info(f"  Adjustment warnings: {len(stats['adjustment_warnings'])}")
        logger.info(f"  Errors: {len(stats['errors'])}")
        if stats['skipped_products']:
            logger.warning(f"  Skipped product IDs: {stats['skipped_products']}")
        if stats['errors']:
            logger.error(f"  Errors: {json.dumps(stats['errors'], ensure_ascii=False)}")
        logger.info("=" * 80)

        return stats

    async def _process_single_receipt(
        self,
        receipt: Any,
        valid_products: Set[str],
        stats: Dict[str, Any]
    ) -> None:
        """Обработать одну поставку"""

        # ============================================================================
        # ЛОГИРОВАНИЕ: Обработка одной поставки
        # ============================================================================
        logger.info("-" * 80)
        logger.info(f"Processing receipt | GUID: {receipt.guid} | DOC: {receipt.document_number}")
        logger.info(f"  Event status: {receipt.event_status}")
        logger.info(f"  Supplier code: {receipt.supplier_code}")
        logger.info(f"  Items count: {len(receipt.supply_data)}")

        # Фильтрация по статусу (оба варианта написания: Ё и Е)
        VALID_STATUSES = ["Проведен", "Проведён"]
        if receipt.event_status not in VALID_STATUSES:
            logger.warning(f"  ❌ SKIPPED: event_status not in {VALID_STATUSES} (actual: '{receipt.event_status}')")
            return

        # Фильтрация по поставщику (исключаем ВБ)
        if receipt.supplier_code == self.EXCLUDED_SUPPLIER_CODE:
            logger.warning(f"  ❌ SKIPPED: supplier is WB (code: {receipt.supplier_code})")
            return

        logger.info(f"  ✅ Receipt passed filters")

        guid = receipt.guid
        document_number = receipt.document_number
        supplier_name = receipt.supplier_name
        supplier_code = receipt.supplier_code
        author = receipt.author_of_the_change

        # Обработать каждый товар в поставке
        # Разделяем на новые (bulk receive) и корректировки (per-item)
        new_items = []  # [(product_id, quantity)]

        for item in receipt.supply_data:
            product_id = item.local_vendor_code
            quantity = float(item.quantity)

            logger.debug(f"    Processing item | Product: {product_id} | Qty: {quantity}")

            # Пропустить несуществующие товары
            if product_id not in valid_products:
                logger.warning(f"    ❌ SKIPPED: product '{product_id}' not found in products table")
                if product_id not in stats["skipped_products"]:
                    stats["skipped_products"].append(product_id)
                continue

            # Проверить: есть ли уже этот товар в этой поставке?
            existing = await self.receipt_repo.get_receipt_item(guid, product_id)

            if existing:
                logger.info(f"    🔄 ADJUSTMENT: {product_id} | Old qty: {existing['quantity']} | New qty: {quantity}")
                # Поставка обновилась — корректировка (per-item, требует проверки остатков)
                await self._adjust_receipt_item(
                    guid=guid,
                    product_id=product_id,
                    old_quantity=float(existing["quantity"]),
                    new_quantity=quantity,
                    document_number=document_number,
                    author=author,
                    stats=stats
                )
                stats["adjusted_movements"] += 1
            else:
                logger.info(f"    ➕ NEW RECEIPT: {product_id} | Qty: {quantity}")
                new_items.append((product_id, quantity))

        # Bulk-создание всех новых receive movements с разбивкой на батчи
        if new_items:
            wms_api_url = getattr(settings, 'WMS_API_URL_MOVEMENTS', 'http://localhost:8000/api/movements')
            BATCH_SIZE = 500  # Лимит WMS API

            total_batches = (len(new_items) + BATCH_SIZE - 1) // BATCH_SIZE
            total_created = 0

            for batch_index in range(0, len(new_items), BATCH_SIZE):
                batch_items = new_items[batch_index:batch_index + BATCH_SIZE]
                batch_number = (batch_index // BATCH_SIZE) + 1

                movements = [
                    {
                        "movement_type": "receive",
                        "product_id": product_id,
                        "quantity": int(quantity),
                        "from_location_code": None,
                        "to_location_code": self.RECEIPT_LOCATION,
                        "batch_number": None,
                        "container_code": None,
                        "user_name": author,
                        "reason": f"Поставка {document_number} от {supplier_name}",
                    }
                    for product_id, quantity in batch_items
                ]

                logger.info(
                    f"Создание movements в WMS | receipt={document_number} | "
                    f"batch={batch_number}/{total_batches} | count={len(movements)}"
                )

                result = await self._create_wms_movements_bulk(
                    api_url=wms_api_url,
                    movements=movements,
                )

                logger.info(
                    f"Movements созданы в WMS | receipt={document_number} | "
                    f"batch={batch_number}/{total_batches} | total={result['total']}"
                )

                for product_id, quantity in batch_items:
                    await self.receipt_repo.create_receipt_item(
                        guid=guid,
                        product_id=product_id,
                        quantity=quantity,
                        document_number=document_number,
                        supplier_name=supplier_name,
                        supplier_code=supplier_code
                    )
                    logger.info(
                        f"Received: {product_id} qty={quantity} "
                        f"from receipt {document_number} (guid={guid})"
                    )

                total_created += result['total']

            stats["created_movements"] += total_created

            if total_batches > 1:
                logger.info(
                    f"✅ Поступление обработано | receipt={document_number} | "
                    f"batches={total_batches} | total_movements={total_created}"
                )

    async def _adjust_receipt_item(
        self,
        guid: str,
        product_id: str,
        old_quantity: float,
        new_quantity: float,
        document_number: str,
        author: str,
        stats: Dict[str, Any]
    ) -> None:
        """Скорректировать товар в поставке"""

        diff = new_quantity - old_quantity

        if diff == 0:
            logger.debug(f"No change for {product_id} in receipt {guid}")
            return

        # Получить доступное количество в зоне приёмки
        available = await self.receipt_repo.get_available_quantity_in_location(
            product_id=product_id,
            location_code=self.RECEIPT_LOCATION
        )

        wms_api_url = getattr(settings, 'WMS_API_URL_MOVEMENTS', 'http://localhost:8000/api/movements')

        if diff > 0:
            # Увеличение количества
            await self._create_wms_movement(
                api_url=wms_api_url,
                movement_type="adjust",
                product_id=product_id,
                to_location_code=self.RECEIPT_LOCATION,
                quantity=abs(diff),
                user_name=author,
                reason=f"Корректировка поставки {document_number}: {old_quantity} → {new_quantity}"
            )
            logger.info(f"Adjusted UP: {product_id} +{diff} (receipt {document_number})")

        else:
            # Уменьшение количества
            required_decrease = abs(diff)

            if available >= required_decrease:
                # Достаточно товара
                await self._create_wms_movement(
                    api_url=wms_api_url,
                    movement_type="adjust",
                    product_id=product_id,
                    from_location_code=self.RECEIPT_LOCATION,
                    quantity=required_decrease,
                    user_name=author,
                    reason=f"Корректировка поставки {document_number}: {old_quantity} → {new_quantity}"
                )
                logger.info(f"Adjusted DOWN: {product_id} -{required_decrease}")

            else:
                # Недостаточно товара — вычитаем сколько можем
                if available > 0:
                    await self._create_wms_movement(
                        api_url=wms_api_url,
                        movement_type="adjust",
                        product_id=product_id,
                        from_location_code=self.RECEIPT_LOCATION,
                        quantity=available,
                        user_name=author,
                        reason=f"Частичная корректировка поставки {document_number}: -{available} из -{required_decrease}"
                    )

                shortage = required_decrease - available
                stats["adjustment_warnings"].append({
                    "guid": guid,
                    "product_id": product_id,
                    "document_number": document_number,
                    "required_decrease": required_decrease,
                    "available": available,
                    "shortage": shortage,
                    "message": f"Не удалось уменьшить на {shortage} шт (доступно только {available})"
                })
                logger.warning(f"Partial adjustment: {product_id} shortage {shortage} in receipt {guid}")

        # Обновить количество в receipt_items
        await self.receipt_repo.update_receipt_item_quantity(
            guid=guid,
            product_id=product_id,
            new_quantity=new_quantity
        )

    async def _create_wms_movement(
        self,
        api_url: str,
        movement_type: str,
        product_id: str,
        quantity: float,
        user_name: str,
        reason: str,
        to_location_code: str = None,
        from_location_code: str = None
    ) -> None:
        """Создать movement через WMS API"""

        payload = {
            "movement_type": movement_type,
            "product_id": product_id,
            "quantity": int(quantity),
            "user_name": user_name,
            "reason": reason,
            "batch_number": None,
            "container_code": None
        }

        if to_location_code:
            payload["to_location_code"] = to_location_code

        if from_location_code:
            payload["from_location_code"] = from_location_code

        # ============================================================================
        # ЛОГИРОВАНИЕ: Вызов WMS API
        # ============================================================================
        logger.debug(f"      📡 WMS API call | URL: {api_url}")
        logger.debug(f"      Payload: {json.dumps(payload, ensure_ascii=False)}")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(api_url, json=payload)
                response.raise_for_status()
                logger.info(f"      ✅ WMS movement created | {movement_type} {product_id} qty={quantity}")

        except httpx.HTTPError as e:
            logger.error(f"      ❌ WMS API ERROR: {e}")
            logger.error(f"      Response: {getattr(e.response, 'text', 'N/A')}")
            raise RuntimeError(f"WMS API error: {e}")

    async def _create_wms_movements_bulk(
        self,
        api_url: str,
        movements: List[dict],
    ) -> dict:
        """Создать несколько movements в WMS одним запросом (bulk)

        Args:
            api_url: Base URL WMS API (например, "http://wms:8310/api/movements")
            movements: Список movements для создания (1-500 элементов)

        Returns:
            Response от WMS API: {"created": [...], "total": N}

        Raises:
            RuntimeError: Если WMS вернул ошибку
        """
        logger.debug(f"      📡 WMS bulk API call | URL: {api_url} | count={len(movements)}")
        logger.debug(f"      Payload: {json.dumps(movements, ensure_ascii=False)}")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    api_url,
                    json=movements,
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                result = response.json()
                logger.info(f"      ✅ WMS bulk movements created | total={result.get('total')}")
                return result
        except httpx.HTTPError as e:
            logger.error(
                f"      ❌ WMS bulk API ERROR | url={api_url} | count={len(movements)} | error={e}"
            )
            logger.error(f"      Response: {getattr(e.response, 'text', 'N/A')}")
            raise RuntimeError(f"WMS bulk API error: {e}")

    async def _get_valid_products(self) -> Set[str]:
        """Получить список валидных product_id из БД"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT id FROM products")
            return {row['id'] for row in rows}
