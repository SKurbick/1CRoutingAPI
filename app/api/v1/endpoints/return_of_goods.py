from typing import List

from fastapi import APIRouter, Depends, status, Body
from app.models.return_of_goods import ReturnOfGoodsData, ReturnOfGoodsResponse, IncomingReturns
from app.service.return_of_goods import ReturnOfGoodsService
from app.dependencies import get_return_of_goods_service

router = APIRouter(prefix="/shipment_of_goods", tags=["Возвраты товаров от клиента WB"])


@router.get("/get_return_of_goods", response_model=List[ReturnOfGoodsData] | ReturnOfGoodsResponse, status_code=status.HTTP_200_OK)
async def get_return_of_goods(
        service: ReturnOfGoodsService = Depends(get_return_of_goods_service)
):
    return await service.get_return_of_goods()

#= Body(example=example_incoming_returns_data)
@router.post("/incoming_returns", response_model=ReturnOfGoodsResponse, status_code=status.HTTP_201_CREATED)
async def get_return_of_goods(
        data: List[IncomingReturns] ,
        service: ReturnOfGoodsService = Depends(get_return_of_goods_service)
):
    return await service.incoming_returns(data)
