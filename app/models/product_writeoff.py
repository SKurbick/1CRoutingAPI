from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field

ProductWriteoffStatus = Literal["pending", "sent", "failed"]


class ProductWriteoffItem(BaseModel):
    product_id: str = Field(..., min_length=1, description="Идентификатор товара из products.id")
    quantity: int = Field(..., gt=0, description="Количество товара для списания")
    comment: str = Field(..., min_length=1, description="Комментарий к списанию")


class ProductWriteoffResponse(BaseModel):
    status: int
    message: str
    request_id: UUID
    item_count: int
    delivery_status: Optional[ProductWriteoffStatus] = None
    details: Optional[str] = None


class ProductWriteoffOperation(BaseModel):
    id: int
    request_id: UUID
    product_id: str
    quantity: int
    comment: str
    delivery_status: ProductWriteoffStatus
    one_c_http_status: Optional[int] = None
    one_c_response: Optional[str] = None
    error_message: Optional[str] = None
    attempt_count: int
    last_attempt_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    sent_at: Optional[datetime] = None


class ProductWriteoffOperationsResponse(BaseModel):
    items: list[ProductWriteoffOperation]
    total: int
    limit: int
    offset: int
