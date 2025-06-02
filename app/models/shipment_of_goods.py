from typing import Optional, List

from pydantic import BaseModel

example_shipment_of_goods_data = [
    {
        'author': 'admin',
        'supply_id': '1231231',
        'product_id': 'wild123',
        'warehouse_id': 1,
        'delivery_type': 'ФБО',
        'wb_warehouse': 'Лентяево',
        'account': 'Хачатрян',
        'quantity': 12,
    }
]


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
    wb_warehouse: str
    account: str
    quantity: int


class ShipmentParamsData(BaseModel):
    products: List[str]
    accounts: List[str]
