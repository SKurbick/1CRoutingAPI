from typing import List, Optional, Any

from pydantic import BaseModel
from datetime import datetime


class ReturnSupplyData(BaseModel):
    local_vendor_code: str
    product_name: str
    quantity: int
    amount_without_vat: float
    amount_with_vat: float


class ReturnToSupplierUpdate(BaseModel):
    guid: str
    supply_guid: str
    document_number: str
    document_created_at: datetime
    return_date: datetime
    event_status: str
    our_organizations_name: str
    update_document_datetime: datetime
    author_of_the_change: str
    supplier_name: str
    supplier_code: str
    currency: str = "RUB"
    supply_data: List[ReturnSupplyData]

    model_config = {
        "json_schema_extra": {
            "examples": [
                [
                    {
                        "guid": "4451ac0d-1bbd-11f1-84f8-50ebf6b2ce7c",
                        "supply_guid": "8b1be364-1893-11f1-84f8-50ebf6b2ce7c",
                        "document_number": "К1ЦБ-000021",
                        "document_created_at": "2026-04-07T09:00:00",
                        "return_date": "2026-04-07T10:00:00",
                        "event_status": "Проведен",
                        "our_organizations_name": "КОНСОЛИДАЦИЯ",
                        "update_document_datetime": "2026-04-07T10:05:00",
                        "author_of_the_change": "Саркисян Геворг",
                        "supplier_name": "Наби Южные Ворота",
                        "supplier_code": "УТ-УТ000083",
                        "currency": "RUB",
                        "supply_data": [
                            {
                                "local_vendor_code": "testwild",
                                "product_name": "[ТЕСТ] Набор контейнеров для специй 4шт прозрачные",
                                "quantity": 10,
                                "amount_without_vat": 5000.0,
                                "amount_with_vat": 6000.0,
                            },
                            {
                                "local_vendor_code": "testwild2",
                                "product_name": "[ТЕСТ] Органайзер для кухонных принадлежностей",
                                "quantity": 5,
                                "amount_without_vat": 2500.0,
                                "amount_with_vat": 3000.0,
                            },
                        ],
                    }
                ]
            ]
        }
    }


class ReturnToSupplierResponse(BaseModel):
    status: int
    message: str
    details: Optional[Any] = None
