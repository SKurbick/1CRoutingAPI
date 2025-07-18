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
from typing import Optional

from pydantic import BaseModel, field_validator
from datetime import datetime


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


class IncomeOnBankAccountResponse(BaseModel):
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
