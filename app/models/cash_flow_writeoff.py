from decimal import Decimal
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CashFlowWriteoff(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "guid": "4b86045d-026e-11f1-84f7-50ebf6b2ce7c",
                "document_number": "ПСЦБ-П000143",
                "date": "2026-02-04T23:59:59",
                "operation_type": "Расход безналичных ДС",
                "organization": "Пилосян Сергей Давидович ИП",
                "operation": "Оплата по кредитам и займам полученным",
                "item_cash_flow": "Возврат краткосрочных займов",
                "expense_item": "Банковские расходы",
                "amount_vat": 46279.56,
                "amount": 679255.80,
                "author": "Пчелинцева Светлана",
                "currency": "RUB",
                "payment_purpose": "Возврат денежных средств по договору факторинга №12026к-24р/ФП от 231224г за дебитора ООО РВБ. В т. ч. НДС (7%) 46279,56 руб.",
                "event_status": "Обработан",
                "bank_status": True,
                "bank_account": "6368 в ООО Вайлдберриз Банк, Пилосян Сергей Давидович ИП"
            }
        }
    )

    guid: str = Field(description="Уникальный идентификатор документа списания ДС")
    document_number: str = Field(description="Номер документа списания ДС")
    date: datetime = Field(description="Дата документа списания ДС")
    operation_type: str = Field(description="Хозяйственная операция из документа списания")
    organization: str = Field(description="Организация из документа")
    operation: str = Field(description="Операция (например: Оплата по кредитам и займам полученным)")
    item_cash_flow: str = Field(description="Статья движения денежных средств")
    expense_item: Optional[str] = Field(default=None, description="Статья расходов — необязательное поле, отсутствует если не заполнено в 1С")
    amount_vat: Optional[Decimal] = Field(default=None, description="Сумма НДС, NUMERIC(17,2) — необязательное поле")
    amount: Decimal = Field(description="Сумма документа, NUMERIC(17,2)")
    author: str = Field(description="Автор документа списания ДС")
    currency: str = Field(description="Валюта (например: RUB, USD)")
    payment_purpose: Optional[str] = Field(default=None, max_length=250, description="Назначение платежа, не более 250 символов — необязательное поле")
    event_status: str = Field(description="Статус проводки из документа списания ДС (например: Обработан)")
    bank_status: bool = Field(description="Статус обработки банком")
    bank_account: str = Field(description="Расчётный счёт организации из документа списания ДС")


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
