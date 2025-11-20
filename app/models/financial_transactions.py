"""
Поступления на Р\С
Дата поступления платежа
Юр лицо (ЛК)
Счет поступления
Банк
Контрагент наименование (от кого поступление)
Контрагент ИНН
сумма
ндс
Назначение платежа
номер платежа
номер документа 1с

income_on_bank_account
Payment receipt date
Legal entity (LE)
Receipt account
Bank
Counterparty name (from whom receipt)
Counterparty INN
Amount
VAT
Payment purpose
Payment number
1C document number

"""
from typing import Optional, List

from pydantic import BaseModel, field_validator
from datetime import datetime

cash_disbursement_order_example = [
    {
        "guid": "8e9b0761-bae2-11f0-84f3-50ebf6b2ce7c",
        "counterparty_name": "Володя Садовод",
        "counterparty_inn": "",
        "our_organizations_name": "КОНСОЛИДАЦИЯ",
        "our_organizations_inn": "7868976987",
        "operation_type": "Оплата поставщику",
        "event_status": "Проведён",
        "document_number_1c": "К1УТ-003172",
        "document_created_at": "2025-11-06 10:31:07",
        "payment_receipt_date": "2025-11-06 10:31:07",
        "payment_request_number": None,
        "currency": "643",
        "author": "Пчелинцева Светлана",
        "payment_descriptions": [
            {
                "payment_object": "Заказ поставщику К1УТ-001561 от 02.08.2025 0:00:00",
                "amount": 579600,
                "vat_rate": "Без НДС",
                "vat": 0
            },
            {
                "payment_object": "Заказ поставщику К1УТ-001588 от 08.08.2025 0:00:00",
                "amount": 420400,
                "vat_rate": "Без НДС",
                "vat": 0
            }
        ]
    }
]

write_off_of_non_cash_funds_example = [
    {
        "guid": "b7dd5f60-be16-11f0-84f3-50ebf6b2ce7c",
        "counterparty_name": "ТАХОСЕРВИС ООО",
        "counterparty_inn": "5029256188",
        "our_organizations_name": "СТАРТ ООО",
        "our_organizations_inn": "5029275624",
        "operation_type": "Оплата поставщику",
        "event_status": "Проведён",
        "document_number_1c": "СТУТ-П000405",
        "document_created_at": "2025-11-10 12:22:07",
        "payment_receipt_date": "2025-11-10 12:22:07",
        "payment_number": "405",
        "payment_date": "2025-11-10 00:00:00",
        "bank_event_status": False,
        "our_organizations_account": "40702810200000000753",
        "receipt_account": "40702810402500066905",
        "payment_request_number": None,
        "currency": "643",
        "payment_purpose": "Оплата по счету № 4172 от 10.09.2025г. за оформление пропусков, внесенных в реестр действующих пропусков. В т.ч. НДС (20%) 1816-67 руб.",
        "author": "Лазаренко Юлия",
        "payment_descriptions": [
            {
                "payment_object": "Списание безналичных ДС СТУТ-П000405 от 10.11.2025 12:22:07",
                "amount": 10900,
                "vat_rate": "20%",
                "vat": 1816.67
            }
        ]
    }
]


class PaymentDescription(BaseModel):
    payment_object: Optional[str] = None
    amount: float
    vat_rate: Optional[str] = None
    vat: float


class WriteOffOfNonCashFunds(BaseModel):
    guid: str
    counterparty_name: str
    counterparty_inn: str
    our_organizations_name: str
    our_organizations_inn: str
    operation_type: str
    event_status: str
    document_number_1c: str
    document_created_at: datetime
    payment_receipt_date: datetime
    payment_number: str
    payment_date: datetime
    bank_event_status: bool
    our_organizations_account: str
    receipt_account: str
    payment_request_number: Optional[str] = None
    currency: str
    payment_purpose: str
    author: str
    payment_descriptions: List[PaymentDescription]


class CashDisbursementOrder(BaseModel):
    guid: str
    counterparty_name: str
    counterparty_inn: str
    our_organizations_name: str
    our_organizations_inn: str
    operation_type: str
    event_status: str
    document_number_1c: str
    document_created_at: datetime
    payment_receipt_date: datetime
    payment_request_number: Optional[str] = None
    currency: str
    author: str
    payment_descriptions: List[PaymentDescription]

class IncomeOnBankAccountUpdate(BaseModel):
    guid: str
    document_created_at: datetime
    payment_receipt_date: datetime
    legal_entity: str
    receipt_account: int
    bank: str
    counterparty_name: str
    counterparty_inn: str
    amount: float
    vat: float
    payment_purpose: str
    payment_number: int
    document_number_1c: str

    @field_validator('counterparty_inn')
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
                return int(value)
            except ValueError:
                raise ValueError(f"Invalid counterparty_inn value: {value}. Must be a number or an empty string.")
        return value


class FinancialTransactionsResponse(BaseModel):
    status: int
    message: str
    details: Optional[str] = None


example_income_on_bank_account_data = [
    {"guid": "84f250ebf6b2ce7d11efb5540f7265c8",
     "document_created_at": "2025-04-16 15:22:37",
     "payment_receipt_date": "2025-04-16 15:00:00",
     "legal_entity": "ИП Даниелян Камо Оганесович (АЛЬФА)",
     "receipt_account": 40802810101060001885.0,
     "bank": "АО \'АЛЬФА-БАНК\'",
     "counterparty_name": "АЛЬФА-БАНК АО (ГО)",
     "counterparty_inn": "772816897112",
     "amount": 1855385,
     "vat": 0,
     "payment_purpose": "Выдача кредита по договору №0A2F9V от 160524  Без НДС",
     "payment_number": 75355,
     "document_number_1c": "К1УТ-000184"}
]
