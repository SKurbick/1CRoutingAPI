from typing import Dict, List, Union, Optional

from pydantic import BaseModel, field_validator
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

example_ordered_goods_from_buyers_data = [
    {"guid": "84f250ebf6b2ce7d11efb5540f7265c8",
     "document_number": "К1УТ-00002533",
     "document_created_at": "2025-04-16 15:22:37",
     "update_document_datetime": "2025-04-16 15:22:37",
     "event_status": "проведен",
     "author_of_the_change": "Артур Пирожков",
     "our_organizations_name": "Консолидация",
     "supply_date": "2025-04-16 15:22:37",
     "supplier_name": "Никола Тесла",
     "supplier_code": "7355608",
     "supply_data": [
         {
             "local_vendor_code": "wild123",
             "product_name": "Название товара",
             "quantity": 123,
             "amount_with_vat": 123,
             "amount_without_vat": 123,
         },
         {
             "local_vendor_code": "wild123",
             "product_name": "Название товара",
             "quantity": 123,
             "amount_with_vat": 123,
             "amount_without_vat": 123,
         }
     ]
     }
]


class SupplyData(BaseModel):
    local_vendor_code: str
    product_name: str
    quantity: float
    amount_with_vat: float
    amount_without_vat: Optional[float] = None


class DocumentData1C(BaseModel):
    supply_date: datetime
    supplier_name: str
    supplier_code: Optional[str] = None
    guid: str
    document_number: str
    document_created_at: datetime
    event_status: str
    update_document_datetime: datetime
    author_of_the_change: str
    our_organizations_name: str


class OrderedGoodsFromBuyersUpdate(DocumentData1C):
    supply_data: List[SupplyData]

    @field_validator('supplier_code')
    def check_at_least_one_provided(cls, value):
        """
        Преобразует counterparty_inn:
        - Если значение пустая строка ("") -> None
        - Если значение строка с числами ("123123123123") -> int
        - Если значение уже int -> оставляет как есть
        """
        if value == "":
            return None
        if isinstance(value, str):
            try:
                return value
            except ValueError:
                raise ValueError(f"Invalid counterparty_inn value: {value}. Must be a number or an empty string.")
        return value


class OrderedGoodsFromBuyersResponse(BaseModel):
    status: int
    message: str
    details: Optional[str] = None


class OrderedGoodsFromBuyersData(DocumentData1C, SupplyData):
    id: int


class IsAcceptanceStatus(BaseModel):
    id: int
    in_acceptance: bool
