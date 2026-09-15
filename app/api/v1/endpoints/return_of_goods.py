import datetime
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, Response, status, Body
from app.models.return_of_goods import (
    IncomingReturns,
    ManualUnidentifiedReturn,
    ReturnOfGoodsData,
    ReturnOfGoodsResponse,
    UnidentifiedGoodsReturn,
)

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
        date_from: datetime.date | None = None,
        service: ReturnOfGoodsService = Depends(get_return_of_goods_service)
):
    return await service.get_return_of_goods(date_from=date_from)


@router.get(
    "/get_unidentified_goods",
    response_model=List[UnidentifiedGoodsReturn] | ReturnOfGoodsResponse,
    status_code=status.HTTP_200_OK,
)
async def get_unidentified_goods(
        date_from: datetime.date | None = None,
        service: ReturnOfGoodsService = Depends(get_return_of_goods_service),
):
    return await service.get_unidentified_goods(date_from=date_from)


@router.post(
    "/receive_unidentified",
    response_model=ReturnOfGoodsResponse,
    status_code=status.HTTP_201_CREATED,
)
async def receive_unidentified(
        background_tasks: BackgroundTasks,
        response: Response,
        data: ManualUnidentifiedReturn,
        service: ReturnOfGoodsService = Depends(get_return_of_goods_service),
):
    result = await service.receive_unidentified(data, background_tasks)
    response.status_code = result.status
    return result

#= Body(example=example_incoming_returns_data)
@router.post("/incoming_returns", response_model=ReturnOfGoodsResponse, status_code=status.HTTP_201_CREATED)
async def get_return_of_goods(
        background_tasks: BackgroundTasks,
        data: List[IncomingReturns] = Body(examples=[example_incoming_returns_data]),
        service: ReturnOfGoodsService = Depends(get_return_of_goods_service)
):
    return await service.incoming_returns(data, background_tasks)
