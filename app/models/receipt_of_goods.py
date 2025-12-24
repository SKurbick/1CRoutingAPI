from typing import List, Optional

from pydantic import BaseModel, field_validator
from datetime import datetime

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

example_add_incoming_receipt_data = [
    {
        "ordered_goods_from_buyers_id": 1,
        "guid": "faabb47d-51ba-11f0-84f2-50ebf6b2ce7d",
        "document_number": "К1УТ-00002533",
        "document_created_at": "2025-04-16 15:22:37",
        "supplier_code": "7355608",
        "supply_data": [
            {
                "local_vendor_code": "wild1333",
                "product_name": "т.Садовая электропила Lithium 150мм с аккумулятором черная 48V (2акк) (ZA286)",
                "quantity": 700,
                "amount_with_vat": 595000,
                "amount_without_vat": 595000
            },
            {
                "local_vendor_code": "wild457",
                "product_name": "т.Поилка для животных переносная 550мл Aqua Dog с ремешком синий (172)",
                "quantity": 180,
                "amount_with_vat": 27900,
                "amount_without_vat": 27900
            },
            {
                "local_vendor_code": "wild332",
                "product_name": "т.Светильник уличный светодиодный 2178T муляж камеры белый",
                "quantity": 50,
                "amount_with_vat": 11500,
                "amount_without_vat": 11500
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
    planned_cost: Optional[float] = None


class OneCModelUpdate(BaseModel):
    guid: str
    supply_data: List[SupplyData]


class ReceiptOfGoodsUpdate(BaseModel):
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
    currency: Optional[str] = None
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


class ReceiptOfGoodsResponse(BaseModel):
    status: int
    message: str
    details: Optional[str] = None


class AddIncomingReceiptUpdate(BaseModel):
    ordered_goods_from_buyers_id: int
    supplier_code: Optional[str] = None
    guid: str
    document_number: str
    document_created_at: datetime
    supply_data: List[SupplyData]
