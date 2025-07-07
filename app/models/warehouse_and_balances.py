from typing import Optional

from pydantic import BaseModel, field_validator
from datetime import datetime

example_defective_goods_data = [
    {"author": "soskanerealka",
     "from_warehouse": 1,
     "to_warehouse": 2,
     "product_id": 'testwild',
     "quantity": 15
     }
]


#
#     author
# supply_id
# product_id
# warehouse_id
# status_id
# quantity
# delivery_type
# transaction_type
# correction_comment

class DefectiveGoodsUpdate(BaseModel):
    author: str
    from_warehouse: int
    to_warehouse: int
    product_id: str
    quantity: int


class DefectiveGoodsResponse(BaseModel):
    status: int
    message: str
    details: Optional[str] = None


class Warehouse(BaseModel):
    id: int
    name: str
    address: Optional[str] = None


class CurrentBalances(BaseModel):
    product_id: str
    warehouse_id: int
    physical_quantity: int
