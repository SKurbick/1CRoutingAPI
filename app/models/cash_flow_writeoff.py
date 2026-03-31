from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime


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
                "amount_vat": 46279.56,
                "amount": 679255.80,
                "author": "Пчелинцева Светлана",
                "currency": "RUB",
                "payment_purpose": "Возврат денежных средств по договору факторинга №12026к-24р/ФП от 231224г за дебитора ООО \"РВБ\". В т. ч. НДС (7%) 46279,56 руб.",
                "status": "Обработан",
                "bank_account": "6368 в ООО \"Вайлдберриз Банк\", Пилосян Сергей Давидович ИП",
            }
        }
    )

    guid: str = Field(description="Уникальный идентификатор документа из 1С (UUID)")
    document_number: str = Field(description="Номер документа списания в 1С")
    date: datetime = Field(description="Дата и время документа")
    operation_type: str = Field(description="Тип операции (например: Списание безналичных ДС)")
    organization: str = Field(description="Наименование организации")
    operation: str = Field(description="Операция (например: Прочие расчёты с контрагентами)")
    item_cash_flow: str = Field(description="Статья движения денежных средств")
    expense_item: Optional[str] = Field(default=None, description="Статья расходов — необязательное поле, может быть null")
    amount_vat: Decimal = Field(description="Сумма НДС, NUMERIC(17,2)")
    amount: Decimal = Field(description="Сумма документа, NUMERIC(17,2)")
    author: str = Field(description="Автор документа")
    currency: str = Field(description="Валюта (например: RUB, USD)")
    payment_purpose: str = Field(max_length=250, description="Назначение платежа, не более 250 символов")
    status: str = Field(description="Статус проводки (например: Проведён)")
    bank_account: str = Field(description="Банковский счёт списания")


class CashFlowWriteoffResponse(BaseModel):
    status: int
    message: str
    details: Optional[str] = None
