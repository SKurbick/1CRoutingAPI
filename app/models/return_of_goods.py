from typing import Optional, List

from pydantic import BaseModel
import datetime


class GoodsReturn(BaseModel):
    id:int
    brand: Optional[str] = None
    dst_office_address: Optional[str] = None
    dst_office_id: Optional[str] = None
    is_status_active: Optional[str] = None
    nm_id: Optional[int] = None
    order_dt: Optional[datetime.datetime] = None
    return_type: Optional[str] = None
    shk_id: Optional[int] = None
    srid: Optional[str] = None
    status: Optional[str] = None
    sticker_id: Optional[int] = None
    subject_name: Optional[str] = None
    tech_size: Optional[int] = None
    account: Optional[str] = None
    date: Optional[datetime.date] = None

class ReturnOfGoodsData(BaseModel):
    product_id: str
    group_data: List[GoodsReturn]


class ReturnOfGoodsResponse(BaseModel):
    status: int
    message: str
    details: Optional[str] = None


class IsReceived(BaseModel):
    id: int
    is_received: bool


class IncomingReturns(BaseModel):
    product_id: str
    sum_quantity: int
    author: str
    warehouse_id: int
    return_date: datetime.date
    is_received_data: List[IsReceived]
