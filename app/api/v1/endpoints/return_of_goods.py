from typing import List

from fastapi import APIRouter, Depends, status, Body
from app.models.return_of_goods import ReturnOfGoodsData, ReturnOfGoodsResponse, IncomingReturns

example_incoming_returns_data = [
    {
        "product_id": "testwild",
        "sum_quantity": 2,
        "author": "Константин",
        "warehouse_id": 1,
        "return_date": "2026-06-18",
        "is_received_data": [
            {
                "srid": "1234567890.0.0",
                "is_received": True
            }
        ],
        "mark_list": [
            {
                "mark_code": "0104607069927654215z9vK9aBcDeF"
            },
            {
                "mark_code": None
            }
        ]
    }
]
from app.service.return_of_goods import ReturnOfGoodsService
from app.dependencies import get_return_of_goods_service

router = APIRouter(prefix="/returns", tags=["Возвраты товаров от клиента WB"])


@router.get("/get_return_of_goods", response_model=List[ReturnOfGoodsData] | ReturnOfGoodsResponse, status_code=status.HTTP_200_OK)
async def get_return_of_goods(
        service: ReturnOfGoodsService = Depends(get_return_of_goods_service)
):
    return await service.get_return_of_goods()

#= Body(example=example_incoming_returns_data)
@router.post("/incoming_returns", response_model=ReturnOfGoodsResponse, status_code=status.HTTP_201_CREATED)
async def get_return_of_goods(
        data: List[IncomingReturns] = Body(examples=[example_incoming_returns_data]),
        service: ReturnOfGoodsService = Depends(get_return_of_goods_service)
):
    return await service.incoming_returns(data)
