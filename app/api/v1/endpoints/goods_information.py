from typing import List
from fastapi import APIRouter, Depends, status, Body, HTTPException, Query

from app.models import UserPermissions
from app.models.goods_information import MetawildsData, metawilds_data_example, AllProductsData, all_products_data_example, GoodsResponse
from app.service.goods_information import GoodsInformationService
from app.dependencies import get_goods_information_service, get_info_from_token

# router = APIRouter(prefix="/income_on_bank_account", dependencies=[Depends(verify_service_token)])


router = APIRouter(prefix="/goods_information", tags=["Информация о товарах"])


@router.get("/get_metawilds_data", response_model=List[MetawildsData], status_code=status.HTTP_200_OK, responses={200: metawilds_data_example})
async def get_metawilds_data(
        user: UserPermissions = Depends(get_info_from_token),
        service: GoodsInformationService = Depends(get_goods_information_service)
):
    if not user.viewing:
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Permission Locked")
    return await service.get_metawilds_data()

@router.get("/get_all_products_data", response_model=List[AllProductsData], status_code=status.HTTP_200_OK, responses={200: all_products_data_example})
async def get_all_products_data(
        user: UserPermissions = Depends(get_info_from_token),
        service: GoodsInformationService = Depends(get_goods_information_service)
):
    if not user.viewing:
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Permission Locked")
    return await service.get_all_products_data()


@router.post("/add_product", response_model=GoodsResponse, status_code=status.HTTP_201_CREATED)
async def add_product(
        data: List[AllProductsData] ,
        user: UserPermissions = Depends(get_info_from_token),
        service: GoodsInformationService = Depends(get_goods_information_service)
):
    if not user.viewing:
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Permission Locked")
    return await service.add_product(data)
