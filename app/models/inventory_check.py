from typing import Optional, List

from pydantic import BaseModel
import datetime

example_inventory_check_data = {
    "author": "Крутой инвентаризовщик",
    "warehouse_id": 1,
    "datetime": "2025-01-01 00:00:00.000",
    "comment": "Плановая инвентаризация",
    "stock_product_data": [
        {
            "product_id": "testwild",
            "quantity": 100
        }
    ]
}


class StockProductData(BaseModel):
    product_id: str
    quantity: int


class InventoryCheckUpdate(BaseModel):
    author: str
    warehouse_id: int
    datetime: datetime.datetime
    comment: str
    stock_product_data:List[StockProductData]


class InventoryCheckResponse(BaseModel):
    status: int
    message: str
    details: Optional[str] = None
