from typing import List, Optional

from pydantic import BaseModel
from datetime import date

group_data_example = [
    {
        "date": "2025-07-16",
        "product_group_data": [
            {
                "product_id": "testwild",
                "shipment_fbo": 0,
                "shipment_fbs": 0,
                "incoming": 0
            },
            {
                "product_id": "wild1075",
                "shipment_fbo": 0,
                "shipment_fbs": 10,
                "incoming": 0
            }
        ]
    },
    {
        "date": "2025-07-17",
        "product_group_data": [
            {
                "product_id": "wild1332",
                "shipment_fbo": 0,
                "shipment_fbs": 0,
                "incoming": 0
            },
            {
                "product_id": "wild1383",
                "shipment_fbo": 0,
                "shipment_fbs": 0,
                "incoming": 100
            }
        ]
    }
]
group_data_response_example = {
    "description": "Сгруппированная информация перемещения товаров",
    "content": {
        "application/json": {
            "example": group_data_example

        }
    },
}


class ProductGroupData(BaseModel):
    product_id: str
    shipment_fbo: int
    shipment_fbs: int
    incoming: int


class ITGroupData(BaseModel):
    date: date
    product_group_data: List[ProductGroupData]


class InventoryTransactionsResponse(BaseModel):
    status: int
    message: str
    details: Optional[str] = None
