"""
WMS Receipt Items Repository
Методы для работы с поступлениями в WMS (таблица wms.receipt_items)
"""

from typing import Optional, Dict, Any
import asyncpg
from asyncpg import Pool


class WMSReceiptRepository:
    """Репозиторий для работы с поступлениями в WMS"""

    def __init__(self, pool: Pool):
        self.pool = pool

    async def get_receipt_item(self, guid: str, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Получить запись о товаре в поставке

        Args:
            guid: GUID документа поставки
            product_id: ID товара

        Returns:
            Dict с данными о товаре в поставке или None
        """
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow(
                """
                SELECT
                    receipt_item_id,
                    guid,
                    product_id,
                    quantity,
                    document_number,
                    supplier_name,
                    supplier_code,
                    document_created_at,
                    supply_date,
                    update_document_datetime,
                    event_status,
                    author_of_the_change,
                    our_organizations_name,
                    order_guid,
                    currency,
                    created_at,
                    updated_at
                FROM wms.receipt_items
                WHERE guid = $1 AND product_id = $2
                """,
                guid,
                product_id
            )
            return dict(result) if result else None

    async def create_receipt_item(
        self,
        guid: str,
        product_id: str,
        quantity: float,
        document_number: str,
        supplier_name: str,
        supplier_code: Optional[str],
        document_created_at: Any,
        supply_date: Any,
        update_document_datetime: Any,
        event_status: str,
        author_of_the_change: str,
        our_organizations_name: str,
        order_guid: Optional[str],
        currency: Optional[str]
    ) -> int:
        """
        Создать запись о новом товаре в поставке

        Returns:
            receipt_item_id созданной записи
        """
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow(
                """
                INSERT INTO wms.receipt_items (
                    guid,
                    product_id,
                    quantity,
                    document_number,
                    supplier_name,
                    supplier_code,
                    document_created_at,
                    supply_date,
                    update_document_datetime,
                    event_status,
                    author_of_the_change,
                    our_organizations_name,
                    order_guid,
                    currency
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                RETURNING receipt_item_id
                """,
                guid,
                product_id,
                quantity,
                document_number,
                supplier_name,
                supplier_code,
                document_created_at,
                supply_date,
                update_document_datetime,
                event_status,
                author_of_the_change,
                our_organizations_name,
                order_guid,
                currency
            )
            return result['receipt_item_id']

    async def update_receipt_item_quantity(
        self,
        guid: str,
        product_id: str,
        new_quantity: float,
        document_number: str,
        supplier_name: str,
        supplier_code: Optional[str],
        document_created_at: Any,
        supply_date: Any,
        update_document_datetime: Any,
        event_status: str,
        author_of_the_change: str,
        our_organizations_name: str,
        order_guid: Optional[str],
        currency: Optional[str]
    ) -> None:
        """
        Обновить количество товара в поставке

        Args:
            guid: GUID документа
            product_id: ID товара
            new_quantity: Новое количество
        """
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE wms.receipt_items
                SET quantity = $3,
                    document_number = $4,
                    supplier_name = $5,
                    supplier_code = $6,
                    document_created_at = $7,
                    supply_date = $8,
                    update_document_datetime = $9,
                    event_status = $10,
                    author_of_the_change = $11,
                    our_organizations_name = $12,
                    order_guid = $13,
                    currency = $14
                WHERE guid = $1 AND product_id = $2
                """,
                guid,
                product_id,
                new_quantity,
                document_number,
                supplier_name,
                supplier_code,
                document_created_at,
                supply_date,
                update_document_datetime,
                event_status,
                author_of_the_change,
                our_organizations_name,
                order_guid,
                currency
            )

    async def get_available_quantity_in_location(
        self,
        product_id: str,
        location_code: str
    ) -> float:
        """
        Получить доступное количество товара в локации

        Args:
            product_id: ID товара
            location_code: Код локации

        Returns:
            Доступное количество (0 если товара нет)
        """
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow(
                """
                SELECT COALESCE(SUM(quantity), 0) as available
                FROM wms.inventory
                WHERE product_id = $1
                  AND location_id = (
                      SELECT location_id
                      FROM wms.locations
                      WHERE location_code = $2
                  )
                  AND status = 'available'
                """,
                product_id,
                location_code
            )
            return float(result['available']) if result else 0.0
