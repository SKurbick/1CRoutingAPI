from typing import List
from fastapi import APIRouter, Depends, status, Body, HTTPException, Query
from app.models.goods_information import (MetawildsData, metawilds_data_example, AllProductsData, all_products_data_example, 
                                          GoodsResponse, ProductInfo, ProductCreate, ProductUpdate)
from app.service.goods_information import GoodsInformationService
from app.dependencies import get_goods_information_service

# router = APIRouter(prefix="/income_on_bank_account", dependencies=[Depends(verify_service_token)])


router = APIRouter(prefix="/goods_information", tags=["Информация о товарах"])


@router.post("/add_product", response_model=GoodsResponse, status_code=status.HTTP_201_CREATED)
async def add_product(
        data: List[ProductCreate] ,
        service: GoodsInformationService = Depends(get_goods_information_service)
):
    return await service.add_product(data)
