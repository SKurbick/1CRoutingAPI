from typing import List

from fastapi import APIRouter, Depends, status, Body, HTTPException

from app.models import UserPermissions
from app.models.return_of_goods import ReturnOfGoodsData, ReturnOfGoodsResponse, IncomingReturns
from app.service.return_of_goods import ReturnOfGoodsService
from app.dependencies import get_return_of_goods_service, get_info_from_token

router = APIRouter(prefix="/returns", tags=["Возвраты товаров от клиента WB"])


@router.get("/get_return_of_goods", response_model=List[ReturnOfGoodsData] | ReturnOfGoodsResponse, status_code=status.HTTP_200_OK)
async def get_return_of_goods(
        user: UserPermissions = Depends(get_info_from_token),
        service: ReturnOfGoodsService = Depends(get_return_of_goods_service)
):
    if not user.viewing:
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Permission Locked")
    return await service.get_return_of_goods()

#= Body(example=example_incoming_returns_data)
@router.post("/incoming_returns", response_model=ReturnOfGoodsResponse, status_code=status.HTTP_201_CREATED)
async def get_return_of_goods(
        data: List[IncomingReturns] ,
        user: UserPermissions = Depends(get_info_from_token),
        service: ReturnOfGoodsService = Depends(get_return_of_goods_service)
):
    if not user.viewing:
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Permission Locked")
    return await service.incoming_returns(data)
