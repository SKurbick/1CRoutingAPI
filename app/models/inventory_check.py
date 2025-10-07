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

inventory_data_example = [
    {
        "date": "2025-07-30",
        "inventory_group_data": [
            {
                "warehouse_id": 1,
                "product_id": "testwild",
                "actual_quantity": 20,
                "check_date": "2025-07-30 15:57:58.040",
                "author": "Абубандит",
                "comment": "Я че знаю я тоже ни че не знаю",
                "created_at": "2025-07-30 15:57:58.040",
                "difference_in_quantity": -100,
            },
            {
                "warehouse_id": 1,
                "product_id": "testwild2",
                "actual_quantity": 10,
                "check_date": "2025-07-30 15:57:58.040",
                "author": "Абубандит",
                "comment": "Я че знаю я тоже ни че не знаю",
                "created_at": "2025-07-30 15:57:58.040",
                "difference_in_quantity": 50,
            },
        ]
    }
]
inventory_data_response_example = {
    "description": "Акты инвентаризации сгруппированный по каждым дням.",
    "content": {
        "application/json": {
            "example": inventory_data_example

        }
    },
}


class InventoryData(BaseModel):
    warehouse_id: int
    product_id: str
    actual_quantity: int
    author: str
    comment: str
    created_at: datetime.datetime
    difference_in_quantity: int



class IDGroupData(BaseModel):
    date: datetime.date
    product_group_data: List[InventoryData]


class InventoryDataResponse(BaseModel):
    pass

class StockProductData(BaseModel):
    product_id: str
    quantity: int


class InventoryCheckUpdate(BaseModel):
    author: str
    warehouse_id: int
    datetime: datetime.datetime
    comment: str
    stock_product_data: List[StockProductData]


class InventoryCheckResponse(BaseModel):
    status: int
    message: str
    details: Optional[str] = None
