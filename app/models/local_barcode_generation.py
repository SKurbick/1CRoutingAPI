
from typing import Dict, List, Union, Optional

from pydantic import BaseModel, field_validator
from datetime import datetime, date

example_goods_acceptance_certificate = {
    "ordered_goods_from_buyers_id": 1,
    "product": "wild123",
    "declared_order_quantity": 150,
    "sum_real_quantity": 150,
    "acceptance_author": "Крутой приемщик",
    "warehouse_id": 1,
    "nested_box_data": [
        {
            "quantity_of_boxes": 30,
            "quantity_in_a_box": 5,
            "is_box": True,
        }
    ]
}
class NestedBox(BaseModel):
    quantity_of_boxes: int
    quantity_in_a_box: int
    is_box: bool

class GoodsAcceptanceCertificateCreate(BaseModel):
    ordered_goods_from_buyers_id:int
    product:str
    declared_order_quantity: int
    sum_real_quantity:int
    acceptance_author: str
    warehouse_id: int
    nested_box_data: List[NestedBox]


class LocalBarcodeGenerationResponse(BaseModel):
    status: str