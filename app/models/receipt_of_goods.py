from typing import Dict, List

from pydantic import BaseModel
from datetime import datetime, date

example_receipt_of_goods_data = [
    {"date": "2025-12-31",
     "wild_data": [
         {"local_vendor_code": "wild123",
          "count": 123},
         {"local_vendor_code": "wild125",
          "count": 125},
     ]
     },
    {"date": "2025-12-30",
     "wild_data": [
         {"local_vendor_code": "wild123",
          "count": 123},
         {"local_vendor_code": "wild125",
          "count": 125},
     ]
     }
]


class WildDataItem(BaseModel):
    local_vendor_code: str
    count: int


class ReceiptOfGoodsUpdate(BaseModel):
    date: date
    wild_data: List[WildDataItem]


class ReceiptOfGoodsResponse(BaseModel):
    status: int
    message: str
