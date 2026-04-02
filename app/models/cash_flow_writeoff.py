from decimal import Decimal
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class PaymentDescription(BaseModel):
    item_cash_flow: Optional[str] = Field(default=None, description="Статья движения денежных средств")
    amount_vat: Optional[Decimal] = Field(default=None, description="Сумма НДС, NUMERIC(17,2)")
    amount: Decimal = Field(description="Сумма, NUMERIC(17,2)")


class CashFlowWriteoff(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "guid": "f14d71fe-210a-11f1-84f9-50ebf6b2ce7c",
                "document_number": "СТЦБ-П001563",
                "date": "2026-03-17T00:00:00",
                "event_status": "Проведен",
                "bank_status": False,
                "operation_type": "Расход безналичных ДС",
                "organization": "СТАРТ ООО",
                "expense_item": "Выплата по ведомости",
                "operation": "Выплата по ведомости на лицевые счета",
                "author": "Дубова Надежда Александровна",
                "currency": "RUB",
                "payment_purpose": "Расчет при увольнении. Без налога (НДС)",
                "bank_account": "5343 в АО \"АЛЬФА-БАНК\", СТАРТ ООО",
                "payment_descriptions": [
                    {
                        "item_cash_flow": "Выплата заработной платы сотрудникам",
                        "amount_vat": 0,
                        "amount": 18327.85
                    }
                ]
            }
        }
    )

    guid: str = Field(description="Уникальный идентификатор документа списания ДС")
    document_number: str = Field(description="Номер документа списания ДС")
    date: datetime = Field(description="Дата документа списания ДС")
    operation_type: str = Field(description="Хозяйственная операция из документа списания")
    organization: str = Field(description="Организация из документа")
    operation: str = Field(description="Операция (например: Оплата поставщику)")
    expense_item: Optional[str] = Field(default=None, description="Статья расходов — необязательное поле, отсутствует если не заполнено в 1С")
    author: str = Field(description="Автор документа списания ДС")
    currency: str = Field(description="Валюта (например: RUB, USD)")
    payment_purpose: Optional[str] = Field(default=None, max_length=250, description="Назначение платежа, не более 250 символов — необязательное поле")
    event_status: str = Field(description="Статус проводки из документа списания ДС (например: Проведен)")
    bank_status: bool = Field(description="Статус обработки банком")
    bank_account: str = Field(description="Расчётный счёт организации из документа списания ДС")
    payment_descriptions: List[PaymentDescription] = Field(description="Список строк документа — каждая строка сохраняется отдельной записью в БД")


class CashFlowWriteoffResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": 200,
                "message": "OK",
                "details": "3 records processed"
            }
        }
    )

    status: int = Field(description="HTTP-статус результата обработки")
    message: str = Field(description="Краткое описание результата")
    details: Optional[str] = Field(default=None, description="Детали обработки или текст ошибки")


class ErrorResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": 500,
                "message": "Internal error",
                "details": "asyncpg: connection refused"
            }
        }
    )

    status: int = Field(description="HTTP-статус ошибки")
    message: str = Field(description="Краткое описание ошибки")
    details: Optional[str] = Field(default=None, description="Детали ошибки")
