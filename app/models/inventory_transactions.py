import datetime
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
                "incoming": 0,
                "re_sorting": 1,
                "returns": 2,
                "moved_to_the_warehouse_defective": 3,
                "received_from_the_warehouse_defective": 2,
                "kit_result": -2
            },
            {
                "product_id": "wild1075",
                "shipment_fbo": 0,
                "shipment_fbs": 10,
                "incoming": 0,
                "re_sorting": 1,
                "returns": 2,
                "moved_to_the_warehouse_defective": 3,
                "received_from_the_warehouse_defective": 2,
                "kit_result": -2
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
                "incoming": 0,
                "re_sorting": 1,
                "returns": 2,
                "moved_to_the_warehouse_defective": 3,
                "received_from_the_warehouse_defective": 2,
                "kit_result": -2
            },
            {
                "product_id": "wild1383",
                "shipment_fbo": 0,
                "shipment_fbs": 0,
                "incoming": 100,
                "re_sorting": 1,
                "returns": 2,
                "moved_to_the_warehouse_defective": 3,
                "received_from_the_warehouse_defective": 2,
                "kit_result": -2
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
    re_sorting: int
    returns: int
    moved_to_the_warehouse_defective: int
    received_from_the_warehouse_defective: int
    kit_result: int
    editing_the_remainder: int


class ITGroupData(BaseModel):
    date: date
    product_group_data: List[ProductGroupData]


class InventoryTransactionsResponse(BaseModel):
    status: int
    message: str
    details: Optional[str] = None


class AddStockByClient(BaseModel):
    product_id: str
    author: str
    warehouse_id: int
    quantity: int
    correction_comment: str


class AddStockByClientGroupData(BaseModel):
    date: date
    product_group_data: List[AddStockByClient]


class KitOperations(BaseModel):
    operation_id: int
    kit_product_id: str
    warehouse_id: int
    operation_type: str
    quantity: int
    status: str
    author: str
    created_at: datetime.datetime

class KitOperationsGroupData(BaseModel):
    date: date
    product_group_data: List[KitOperations]


class IncomingReturns(BaseModel):
    operation_id: int
    author: str
    product_id: str
    warehouse_id: int
    quantity: int
    created_at: datetime.datetime

class IncomingReturnsGroupData(BaseModel):
    date: date
    product_group_data: List[IncomingReturns]


class ReSortingOperation(BaseModel):
    operation_id: int
    from_product_id: str
    to_product_id: str
    warehouse_id: int
    quantity: int
    reason: str
    created_at: datetime.datetime
    author: str
    operation_status: str

class ReSortingOperationGroupData(BaseModel):
    date: date
    product_group_data: List[ReSortingOperation]


add_stock_by_client_response_example = ...
kit_operations_response_example = ...
incoming_returns_response_example = ...
re_sorting_operations_response_example = ...
