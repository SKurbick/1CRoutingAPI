from typing import Annotated, List, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import Field

from app.dependencies.product_writeoff import get_product_writeoff_service
from app.models.product_writeoff import (
    ProductWriteoffItem,
    ProductWriteoffOperationsResponse,
    ProductWriteoffResponse,
)
from app.service.product_writeoff import ProductWriteoffService

router = APIRouter(prefix="/product_writeoff", tags=["Списание товаров в 1С"])


@router.post(
    "/update",
    response_model=ProductWriteoffResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Списать товары и передать данные в 1С",
)
async def create_product_writeoff(
    data: Annotated[List[ProductWriteoffItem], Field(min_length=1)],
    service: ProductWriteoffService = Depends(get_product_writeoff_service),
) -> ProductWriteoffResponse:
    result = await service.process(data)
    if result.status >= 400:
        raise HTTPException(status_code=result.status, detail=result.model_dump(mode="json"))
    return result


@router.post(
    "/{request_id}/retry",
    response_model=ProductWriteoffResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Повторно отправить неудачное списание в 1С",
)
async def retry_product_writeoff(
    request_id: UUID,
    service: ProductWriteoffService = Depends(get_product_writeoff_service),
) -> ProductWriteoffResponse:
    result = await service.retry(request_id)
    if result.status >= 400:
        raise HTTPException(status_code=result.status, detail=result.model_dump(mode="json"))
    return result


@router.get(
    "/operations",
    response_model=ProductWriteoffOperationsResponse,
    summary="Получить операции списания",
)
async def get_product_writeoff_operations(
    product_id: str | None = Query(default=None, min_length=1),
    statuses: List[Literal["pending", "sent", "failed"]] | None = Query(
        default=None,
        alias="status",
    ),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    service: ProductWriteoffService = Depends(get_product_writeoff_service),
) -> ProductWriteoffOperationsResponse:
    return await service.get_operations(
        product_id=product_id,
        statuses=statuses,
        limit=limit,
        offset=offset,
    )
