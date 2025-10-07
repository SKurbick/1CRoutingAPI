from pydantic import BaseModel

docs_data_response_example = ...


from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime

class ServiceItem(BaseModel):
    """Model for service item"""
    # description: str = Field(..., alias="Услуга")
    description: str
    price_without_vat: float = Field(..., alias="Стоимость без НДС")
    price_with_vat: float = Field(..., alias="Стоимость с НДС")
    # tax_rate: str = Field(..., alias="Налоговая ставка")
    tax_rate: Optional[str] = Field(None, alias="Налоговая ставка")  # Сделали опциональным

    # class Config:
    #     validate_by_name = True
    #     populate_by_name = True

class DocsData(BaseModel):
    """Main invoice data model"""
    invoice_number: str = Field(..., alias="Счёт фактура номер")
    invoice_date: str = Field(..., alias="Счёт фактура дата")
    seller_name: str = Field(..., alias="Наименование продавца")
    seller_inn: str = Field(..., alias="ИНН продавца")
    seller_kpp: str = Field(..., alias="КПП продавца")
    buyer_name: str = Field(..., alias="Наименование покупателя")
    buyer_inn: str = Field(..., alias="ИНН покупателя")
    buyer_kpp: Optional[str] = Field("", alias="КПП покупателя")
    services: List[ServiceItem] = Field(..., alias="Услуги")
    inner_zip_name: str
    # pdf_base64: str

    class Config:
        # validate_by_name = True
        populate_by_name = True