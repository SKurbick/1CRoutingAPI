from typing import Optional, List

from pydantic import BaseModel, Field, field_validator
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


class UnidentifiedGoodsReturn(GroupDataGoodsReturns):
    product_id: str = "не найден артикул продавца по артикулу wb"
    identification_error: str
    status_history_found: bool


class ReturnOfGoodsResponse(BaseModel):
    status: int
    message: str
    details: Optional[str] = None


class IsReceived(BaseModel):
    srid: str
    is_received: bool


class MarkCode(BaseModel):
    mark_code: str = "broken"

    @field_validator("mark_code", mode="before")
    @classmethod
    def default_broken_for_null(cls, value):
        return "broken" if value is None else value


class IncomingReturns(BaseModel):
    product_id: str
    sum_quantity: int
    author: str
    warehouse_id: int
    return_date: date
    is_received_data: List[IsReceived]
    mark_list: Optional[List[MarkCode]] = None


class ManualUnidentifiedReturn(BaseModel):
    product_id: str = Field(min_length=1, max_length=50)
    warehouse_id: int = Field(gt=0)
    return_date: date
    author: str = Field(min_length=1, max_length=50)
    comment: Optional[str] = Field(default=None, max_length=2000)
    srids: List[str] = Field(min_length=1)
    mark_list: Optional[List[MarkCode]] = None

    @field_validator("srids")
    @classmethod
    def srids_must_be_unique(cls, value: List[str]) -> List[str]:
        value = [srid.strip() for srid in value]
        if any(not srid for srid in value):
            raise ValueError("srids must not be blank")
        if len(value) != len(set(value)):
            raise ValueError("srids must be unique")
        return value


# class OneCReturnData(BaseModel):

class OneCReturnDataByProduct(BaseModel):
    product_id: str
    product_name: str
    quantity: int
    mark_list: Optional[List[MarkCode]] = None
    # return_data: List[OneCReturnData]

class ReturnsOneCModelAdd(BaseModel):
    account: str
    author: str
    inn: str
    # return_date: date
    return_date: str
    return_data_by_product: List[OneCReturnDataByProduct]


data =  [
    {
        "account": "Вектор",
        "author": "Константин",
        "inn": 123123123123,
        "return_date": "2025-09-12",
        "return_data_by_product":[
            {
                "product_id": "wild123",
                "product_name": "название товара",
                "quantity": 2
            },
            {
                "product_id": "wild150",
                "product_name": "название товара",
                "quantity": 5
            }
        ]
    },
    {
        "account": " Тоноян",
        "inn": 123123123123,
        "author": "Константин",
        "return_date": "2025-09-12",
        "return_data_by_product": [
            {
                "product_id": "wild123",
                "product_name": "название товара",
                "quantity": 2
            }
        ]
    }
]