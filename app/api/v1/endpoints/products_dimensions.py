from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from app.dependencies import get_product_dimensions_service, get_info_from_token
from app.models import UserPermissions
from app.models.products_dimensions import ProductDimensions, ProductDimensionsUpdate
from app.service.products_dimensions import ProductDimensionsService

router = APIRouter(prefix="/products_dimensions", tags=["product-dimensions"])


@router.get("/{product_id}", response_model=ProductDimensions)
async def get_product_dimensions(
    product_id: str,
    user: UserPermissions = Depends(get_info_from_token),
    service: ProductDimensionsService = Depends(get_product_dimensions_service)
):
    """Получить габариты товара"""
    if not user.viewing:
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Permission Locked")
    dimensions = await service.get_product_dimensions(product_id)
    if not dimensions:
        raise HTTPException(
            status_code=404,
            detail=f"Габариты для товара {product_id} не найдены"
        )
    return dimensions


@router.put("/{product_id}", response_model=ProductDimensions)
async def update_product_dimensions(
    product_id: str,
    update_data: ProductDimensionsUpdate,
    user: UserPermissions = Depends(get_info_from_token),
    service: ProductDimensionsService = Depends(get_product_dimensions_service)
):
    """Обновить габариты товара"""
    if not user.viewing:
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Permission Locked")
    updated = await service.update_product_dimensions(product_id, update_data)
    if not updated:
        raise HTTPException(
            status_code=404,
            detail=f"Товар {product_id} не найден"
        )
    return updated


@router.get("/", response_model=list[ProductDimensions])
async def get_all_product_dimensions(
    user: UserPermissions = Depends(get_info_from_token),
    service: ProductDimensionsService = Depends(get_product_dimensions_service)
):
    """Получить все габариты товаров"""
    if not user.viewing:
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Permission Locked")
    return await service.get_all_product_dimensions()
