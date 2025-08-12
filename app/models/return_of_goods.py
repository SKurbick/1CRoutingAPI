from typing import Optional, List

from pydantic import BaseModel
from datetime import datetime, date


class GoodsReturn(BaseModel):
    # Поля из goods_returns_dev
    srid: str
    account: Optional[str] = None
    barcode: Optional[str] = None
    brand: Optional[str] = None
    dst_office_address: Optional[str] = None
    dst_office_id: Optional[int] = None
    nm_id: Optional[int] = None
    order_dt: Optional[date] = None  # тип DATE в БД
    order_id: Optional[int] = None
    return_type: Optional[str] = None
    shk_id: Optional[int] = None
    sticker_id: Optional[str] = None  # в БД — varchar, не int!
    subject_name: Optional[str] = None
    tech_size: Optional[str] = None  # в БД — varchar(255), например '42', 'L', 'XL'
    reason: Optional[str] = None
    is_status_active: Optional[int] = None  # в БД — int4, не bool
    goods_created_at: Optional[datetime] = None  # renamed from `created_at` → `goods_created_at`
    is_received: Optional[bool] = None


class GoodsReturnsStatusHistory(BaseModel):
    # Поля из goods_returns_status_history
    status: Optional[str] = None
    status_dt: Optional[datetime] = None
    completed_dt: Optional[datetime] = None
    expired_dt: Optional[datetime] = None
    ready_to_return_dt: Optional[datetime] = None
    status_created_at: Optional[datetime] = None  # renamed from `created_at`


class GroupDataGoodsReturns(GoodsReturn, GoodsReturnsStatusHistory):
    pass


class ReturnOfGoodsData(BaseModel):
    product_id: str
    group_data: List[GroupDataGoodsReturns]


class ReturnOfGoodsResponse(BaseModel):
    status: int
    message: str
    details: Optional[str] = None


class IsReceived(BaseModel):
    srid: str
    is_received: bool


class IncomingReturns(BaseModel):
    product_id: str
    sum_quantity: int
    author: str
    warehouse_id: int
    return_date: date
    is_received_data: List[IsReceived]
