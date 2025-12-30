from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, computed_field

from app.models.containers import Container


class ProductDimensionsBase(BaseModel):
    """Базовая модель габаритов товара"""

    length: Optional[int] = Field(None, ge=0, description="Длина товара (см)")
    width: Optional[int] = Field(None, ge=0, description="Ширина товара (см)")
    height: Optional[int] = Field(None, ge=0, description="Высота товара (см)")
    wb_length: Optional[int] = Field(None, ge=0, description="Длина для маркетплейса (см)")
    wb_width: Optional[int] = Field(None, ge=0, description="Ширина для маркетплейса (см)")
    wb_height: Optional[int] = Field(None, ge=0, description="Высота для маркетплейса (см)")
    container_id: Optional[int] = Field(None, description="ID коробки/контейнера")
    items_per_box: Optional[int] = Field(None, ge=0, description="Количество товара в коробке.")


class ProductDimensionsUpdate(ProductDimensionsBase):
    """Схема для обновления (только изменяемые поля)"""


class ProductDimensionsInDB(ProductDimensionsBase):
    """Модель с полями из БД"""

    id: int
    product_id: str
    volume: Optional[float] = Field(None, description="Объем товара (л)")
    wb_volume: Optional[float] = Field(None, description="Объем для маркетплейса (л)")
    created_at: datetime
    updated_at: datetime


class ProductDimensions(ProductDimensionsInDB):
    """Основная модель для ответов API"""

    product_name: Optional[str] = Field(None, description="Название товара из products")
    container: Optional[Container] = Field(None, description="Информация о коробке")

    @computed_field
    @property
    def total_items_per_pallet(self) -> Optional[int]:
        """Общее количество товара на паллете (вычисляемое поле)"""
        if self.items_per_box and self.container and self.container.boxes_per_pallet:
            return self.items_per_box * self.container.boxes_per_pallet
        return None
