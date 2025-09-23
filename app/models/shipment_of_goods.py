import datetime
from typing import Optional, List
from enum import Enum

from pydantic import BaseModel

example_shipment_of_goods_data = [
    {
        'author': 'admin',
        'supply_id': '1231231',
        'product_id': 'wild123',
        'warehouse_id': 1,
        'delivery_type': 'ФБО',
        'shipment_date': '2025-07-06',
        'wb_warehouse': 'Лентяево',
        'account': 'Хачатрян',
        'quantity': 12,
        "product_reserves_id": 11
    }
]


class DeliveryType(str, Enum):
    FBS = "ФБС"
    FBO = "ФБО"


class ShipmentOfGoodsResponse(BaseModel):
    status: int
    message: str
    details: Optional[str] = None


class ShipmentOfGoodsUpdate(BaseModel):
    author: str
    supply_id: str
    product_id: str
    warehouse_id: int
    delivery_type: str
    wb_warehouse: Optional[str] = None
    account: str
    quantity: int
    shipment_date: Optional[datetime.date] = None
    product_reserves_id: Optional[int] = None


class ShipmentParamsData(BaseModel):
    products: List[str]
    accounts: List[str]


class ReserveOfGoodsResponse(BaseModel):
    supply_id: Optional[str] = None
    product_reserves_id: Optional[int] = None


class ReserveOfGoodsCreate(BaseModel):
    product_id: str
    warehouse_id: int
    ordered: int
    account: str
    delivery_type: str
    wb_warehouse: Optional[str] = None
    reserve_date: datetime.date
    supply_id: str
    expires_at: datetime.datetime


class ShippedGoods(BaseModel):
    supply_id: str
    quantity_shipped: int


class ShippedGoodsByID(BaseModel):
    reserve_id: int
    quantity_shipped: int
    is_fulfilled: bool


example_shipped_goods_data = [
    {
        "supply_id": "WB-GI-166715280",
        "quantity_shipped": 5
    }
]

example_reserve_of_goods_data = [
    {
        "product_id": "testwild",
        "warehouse_id": 1,
        "ordered": 20,
        "account": "Тоноян",
        "delivery_type": "ФБС",
        "wb_warehouse": "Писюлькино",
        "supply_id": "WB-GI-166715280",
        "reserve_date": "2025-07-25",
        "expires_at": "2025-08-05 16:08:57.089858",
    }
]

shipment_data_response_example = {

}


class ReservedData(BaseModel):
    reserve_id: int
    product_id: str
    warehouse_id: int
    ordered: int
    shipped: int
    account: str
    delivery_type: str
    wb_warehouse: Optional[str] = None
    supply_id: str
    reserve_date: datetime.date
    # created_at
    # expires_at
    is_fulfilled: bool




data = [
    {
        "product_id": "wild123",
        "delivery_type_data": [
            {
                "reserve_type": "ФБО",
                "current_reserve": 12},
            {
                "reserve_type": "ФБО",
                "current_reserve": 12},
        ]

    }
]

class DeliveryTypeData(BaseModel):
    reserve_type: str
    current_reserve: int

class SummReserveData(BaseModel):
    product_id: str
    delivery_type_data: List[DeliveryTypeData]