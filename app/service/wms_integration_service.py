"""
WMS Integration Service
Обработка поступлений из 1С и создание movements в WMS
"""

import logging
from typing import List, Dict, Any, Set
import httpx
from app.dependencies.config import settings

logger = logging.getLogger(__name__)


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

        return stats

    async def _process_single_receipt(
        self,
        receipt: Any,
        valid_products: Set[str],
        stats: Dict[str, Any]
    ) -> None:
        """Обработать одну поставку"""

        # Фильтрация по статусу
        if receipt.event_status != "Проведен":
            logger.debug(f"Skipping receipt {receipt.guid}: status={receipt.event_status}")
            return

        # Фильтрация по поставщику (исключаем ВБ)
        if receipt.supplier_code == self.EXCLUDED_SUPPLIER_CODE:
            logger.debug(f"Skipping receipt {receipt.guid}: supplier is WB")
            return

        guid = receipt.guid
        document_number = receipt.document_number
        supplier_name = receipt.supplier_name
        supplier_code = receipt.supplier_code
        author = receipt.author_of_the_change

        # Обработать каждый товар в поставке
        for item in receipt.supply_data:
            product_id = item.local_vendor_code
            quantity = float(item.quantity)

            # Пропустить несуществующие товары
            if product_id not in valid_products:
                logger.warning(f"Product {product_id} not found in products table, skipping")
                if product_id not in stats["skipped_products"]:
                    stats["skipped_products"].append(product_id)
                continue

            # Проверить: есть ли уже этот товар в этой поставке?
            existing = await self.receipt_repo.get_receipt_item(guid, product_id)

            if existing:
                # Поставка обновилась — корректировка
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
                # Новая поставка — receive
                await self._receive_goods(
                    guid=guid,
                    product_id=product_id,
                    quantity=quantity,
                    document_number=document_number,
                    supplier_name=supplier_name,
                    supplier_code=supplier_code,
                    author=author
                )
                stats["created_movements"] += 1

    async def _receive_goods(
        self,
        guid: str,
        product_id: str,
        quantity: float,
        document_number: str,
        supplier_name: str,
        supplier_code: str,
        author: str
    ) -> None:
        """Приходовать товар (новая поставка)"""

        # Создать movement через WMS API
        wms_api_url = getattr(settings, 'WMS_API_URL_MOVEMENTS', 'http://localhost:8000/api/movements')

        await self._create_wms_movement(
            api_url=wms_api_url,
            movement_type="receive",
            product_id=product_id,
            to_location_code=self.RECEIPT_LOCATION,
            quantity=quantity,
            user_name=author,
            reason=f"Поставка {document_number} от {supplier_name}"
        )

        # Сохранить в receipt_items
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

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(api_url, json=payload)
                response.raise_for_status()
                logger.debug(f"Created WMS movement: {movement_type} {product_id} qty={quantity}")

        except httpx.HTTPError as e:
            logger.error(f"Failed to create WMS movement: {e}")
            raise RuntimeError(f"WMS API error: {e}")

    async def _get_valid_products(self) -> Set[str]:
        """Получить список валидных product_id из БД"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT id FROM products")
            return {row['id'] for row in rows}
