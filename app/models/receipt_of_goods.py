from typing import Dict, List, Union, Optional

from pydantic import BaseModel
from datetime import datetime, date

"""
Номер документа - document_number
дата  - date
wild  - local_vendor_code
количество - quantity
сумма с НДС - amount_with_vat
Без НДС  - amount_without_vat
Наименование поставщика  - supplier_name
Код пост-ка  - supplier_code
дата изменения док-та  - update_document_datetime
автор изменения - author_of_the_change
Наименование нашей организации - our_organizations_name
"""

example_receipt_of_goods_data = [
    {"guid": "84f250ebf6b2ce7d11efb5540f7265c8",
     "document_number": "К1УТ-00002533",
     "document_created_at": "2025-04-16 15:22:37",
     "update_document_datetime": "2025-04-16 15:22:37",
     "event_status": "проведен",
     "supply_data": [
         {"supply_date": "2025-04-16 15:22:37",
          "local_vendor_code": "wild123",
          "quantity": 123,
          "amount_with_vat": 123,
          "amount_without_vat": 123,
          "supplier_name": "Никола Тесла",
          "supplier_code": "7355608"},
         {"supply_date": "2025-04-16 15:22:37",
          "local_vendor_code": "wild123",
          "quantity": 123,
          "amount_with_vat": 123,
          "amount_without_vat": 123,
          "supplier_name": "Никола Тесла",
          "supplier_code": "7355608"
          }
     ],
     "author_of_the_change": "Артур Пирожков",
     "our_organizations_name": "Консолидация"}
]


class ReceiptOfGoodsUpdate(BaseModel):
    document_number: str
    date: date
    local_vendor_code: str
    quantity: int
    amount_with_vat: int
    amount_without_vat: Optional[int] = None
    supplier_name: str
    supplier_code: Optional[str] = None
    update_document_datetime: datetime
    author_of_the_change: str
    our_organizations_name: str


class ReceiptOfGoodsResponse(BaseModel):
    status: int
    message: str
