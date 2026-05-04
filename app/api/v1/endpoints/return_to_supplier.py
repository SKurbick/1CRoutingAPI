from typing import List, Annotated

from fastapi import APIRouter, Depends, Body

from app.dependencies.return_to_supplier import get_return_to_supplier_service
from app.models.return_to_supplier import ReturnToSupplierUpdate, ReturnToSupplierResponse
from app.service.return_to_supplier import ReturnToSupplierService

router = APIRouter(prefix="/return_to_supplier", tags=["Возвраты товаров поставщику"])

_example_data = [
    {
        "guid": "test4451ac0d-1bbd-11f1-84f8-50ebf6b2ce7c",
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


@router.post("/update", response_model=ReturnToSupplierResponse, status_code=200)
async def update_return_to_supplier(
    data: Annotated[
        List[ReturnToSupplierUpdate],
        Body(
            openapi_examples={
                "test_return": {
                    "summary": "Возврат двух позиций поставщику (тестовые данные)",
                    "value": _example_data,
                }
            }
        ),
    ],
    service: ReturnToSupplierService = Depends(get_return_to_supplier_service),
):
    """
    Актуализация документов возврата товаров поставщику из 1С.
    Алгоритм:
    1. По guid инвалидируем существующие записи (is_valid = FALSE)
    2. Вставляем строки документа (денормализованно, одна строка = один товар)
    3. Обновляем позиции в return_to_supplier_items для расчёта остатков
    """
    return await service.create_data(data)
