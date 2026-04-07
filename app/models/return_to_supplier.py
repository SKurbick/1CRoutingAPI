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
    supply_date: datetime
    guid: str
    supply_guid: str
    supplier_name: str
    supplier_code: str
    event_status: str
    our_organizations_name: str
    document_number: str
    update_document_datetime: datetime
    author_of_the_change: str
    currency: str = "RUB"
    supply_data: List[ReturnSupplyData]


class ReturnToSupplierResponse(BaseModel):
    status: str
    message: str
    details: Optional[Any] = None
