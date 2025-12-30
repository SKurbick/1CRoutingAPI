from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class ContainerBase(BaseModel):
    name: Optional[str] = Field(None, max_length=255, description="Название коробки")
    length: float = Field(..., gt=0, description="Длина в см (с точностью до мм)")
    width: float = Field(..., gt=0, description="Ширина в см (с точностью до мм)")
    height: float = Field(..., gt=0, description="Высота в см (с точностью до мм)")
    boxes_per_pallet: Optional[int] = Field(None, ge=0, description="Количество коробок на паллете")


class ContainerCreate(ContainerBase):
    pass


class ContainerUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    length: Optional[float] = Field(None, gt=0, decimal_places=1, max_digits=6)
    width: Optional[float] = Field(None, gt=0, decimal_places=1, max_digits=6)
    height: Optional[float] = Field(None, gt=0, decimal_places=1, max_digits=6)
    boxes_per_pallet: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class ContainerInDB(ContainerBase):
    id: int
    volume: float
    is_active: bool
    created_at: datetime
    updated_at: datetime


class Container(ContainerInDB):
    pass
