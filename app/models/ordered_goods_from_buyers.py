from typing import List, Optional

from pydantic import BaseModel, field_validator
from datetime import datetime
from app.models.local_barcode_generation import GoodsAcceptanceCertificateCreate

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
     "expected_receipt_date": datetime.today(),
     "currency": "string",
     "shipment_date": datetime.today(),
     "payment_document_number": "string",
     "payment_indicator": "string",
     "receipt_transaction_number": "string",
     "comment": "string",
     "supply_data": [
         {
             "local_vendor_code": "wild123",
             "product_name": "Название товара",
             "quantity": 123,
             "amount_with_vat": 123,
             "amount_without_vat": 123,
             "actual_quantity": 123,
             "unit_price": 123.2,
             "last_purchase_supplier": "string",
             "last_purchase_price": 123.1,
             "cancelled_due_to": "string"
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

ordered_goods_and_printed_data_example = {
    "ordered_of_goods_data": [
        {
            "local_vendor_code": "wild1510",
            "product_name": "т.Велотренажер Armed HJ-088A",
            "quantity": 422,
            "amount_with_vat": 244760,
            "amount_without_vat": 244760,
            "photo_link": "https://basket-20.wbbasket.ru/vol3440/part344061/344061421/images/tm/1.webp",
            "supply_date": "2025-06-16T17:51:53",
            "supplier_name": "Другие поставщики",
            "supplier_code": None,
            "guid": "7048d107-4ac1-11f0-84f2-50ebf6b2ce7d",
            "document_number": "К1УТ-001222",
            "document_created_at": "2025-06-16T17:51:53",
            "event_status": "Проведён",
            "update_document_datetime": "2025-06-16T17:51:53",
            "author_of_the_change": "Котова Евгения",
            "our_organizations_name": "КОНСОЛИДАЦИЯ",
            "id": 1
        },
        {
            "local_vendor_code": "wild1555",
            "product_name": "т.Вентилятор раскладной 180 Wind Waver",
            "quantity": 740,
            "amount_with_vat": 481000,
            "amount_without_vat": 481000,
            "photo_link": "https://basket-23.wbbasket.ru/vol4006/part400670/400670677/images/tm/1.webp",
            "supply_date": "2025-06-17T16:41:11",
            "supplier_name": "Назима",
            "supplier_code": None,
            "guid": "ba6105b7-4b80-11f0-84f2-50ebf6b2ce7d",
            "document_number": "К1УТ-001228",
            "document_created_at": "2025-06-17T16:41:11",
            "event_status": "Проведён",
            "update_document_datetime": "2025-06-17T16:41:18",
            "author_of_the_change": "Ширыкалов Максим Андреевич",
            "our_organizations_name": "КОНСОЛИДАЦИЯ",
            "id": 14
        }
    ],
    "printed_barcode_data": [
        {
            "ordered_goods_from_buyers_id": 1,
            "product": "wild123",
            "product_name": "т.Велотренажер Armed HJ-088A",
            "declared_order_quantity": 15,
            "sum_real_quantity": 15,
            "acceptance_author": "Крутой приемщик",
            "warehouse_id": 1,
            "added_photo_link": "https://avatars.mds.yandex.net/i?id=05331e8b60e705232516150f16faa955_l-10148308-images-thumbs&n=13",
            "supplier_code": None,
            "guid": "ba6105b7-4b80-11f0-84f2-50ebf6b2ce7d",
            "document_number": "К1УТ-001228",
            "document_created_at": "2025-06-17T16:41:11",
            "nested_box_data": [
                {
                    "quantity_of_boxes": 3,
                    "quantity_in_a_box": 3,
                    "is_box": True
                },
                {
                    "quantity_of_boxes": 2,
                    "quantity_in_a_box": 3,
                    "is_box": True
                }
            ],
            "photo_link": None
        }
    ]
}



class ReceiptsData(BaseModel):
    reciept_number: str
    reciept_date: datetime
    reciept_quantity: float
    reciept_amount: float


class SupplyData(BaseModel):
    local_vendor_code: str
    product_name: str
    quantity: float
    amount_with_vat: float
    amount_without_vat: Optional[float] = None
    photo_link: Optional[str] = None
    actual_quantity: Optional[int] = None
    unit_price: Optional[float] = None
    last_purchase_supplier: Optional[str] = None
    last_purchase_price: Optional[float] = None
    cancelled_due_to: Optional[str] = None
    reciepts: list[ReceiptsData]


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
    expected_receipt_date: Optional[datetime] = None
    currency: Optional[str] = None
    shipment_date: Optional[datetime] = None
    payment_document_number: Optional[str] = None
    payment_indicator: Optional[str] = None
    receipt_transaction_number: Optional[str] = None
    comment: Optional[str] = None


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


class PrintedBarcodeData(GoodsAcceptanceCertificateCreate):
    guid: str
    document_number: str
    document_created_at: datetime
    amount_with_vat: float
    amount_without_vat: Optional[float] = None
    supplier_code: Optional[str] = None
    photo_link: Optional[str] = None


class OrderedGoodsAndPrintedBarcodeData(BaseModel):
    ordered_of_goods_data: List[OrderedGoodsFromBuyersData]
    printed_barcode_data: List[None | PrintedBarcodeData]
