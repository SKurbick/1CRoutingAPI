
from typing import List, Optional

from pydantic import BaseModel

example_goods_acceptance_certificate = {
    "ordered_goods_from_buyers_id": 1,
    "product": "wild123",
    "product_name": "съедобные трусы",
    "declared_order_quantity": 150,
    "sum_real_quantity": 150,
    "acceptance_author": "Крутой приемщик",
    "warehouse_id": 1,
    "photo_link":"https://avatars.mds.yandex.net/i?id=05331e8b60e705232516150f16faa955_l-10148308-images-thumbs&n=13",
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
    product_name: str
    declared_order_quantity: int
    sum_real_quantity:int
    acceptance_author: str
    warehouse_id: int
    added_photo_link: Optional[str] = None
    nested_box_data: List[NestedBox]


class LocalBarcodeGenerationResponse(BaseModel):
    status: str