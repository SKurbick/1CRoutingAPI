import datetime
from typing import List
# OrderedGoodsFromBuyers
from fastapi import APIRouter, Depends, status, Body, HTTPException
from app.models.ordered_goods_from_buyers import OrderedGoodsFromBuyersUpdate, OrderedGoodsFromBuyersResponse, example_ordered_goods_from_buyers_data, \
    OrderedGoodsFromBuyersData, IsAcceptanceStatus
from app.service.ordered_goods_from_buyers import OrderedGoodsFromBuyersService
from app.dependencies import get_ordered_goods_from_buyers_service
from app.dependencies.security import verify_service_token

# router = APIRouter(prefix="/income_on_bank_account", dependencies=[Depends(verify_service_token)])


router = APIRouter(prefix="/ordered_goods_from_buyers", tags=["Заказы товаров у поставщиков"])


@router.post("/update", response_model=OrderedGoodsFromBuyersResponse, status_code=status.HTTP_201_CREATED)
async def create_data(
        data: List[OrderedGoodsFromBuyersUpdate] = Body(example=example_ordered_goods_from_buyers_data),
        service: OrderedGoodsFromBuyersService = Depends(get_ordered_goods_from_buyers_service)
):
    result = await service.create_data(data)

    if result.status >= 400:
        raise HTTPException(
            status_code=result.status,
            detail={
                "message": result.message,
                "details": result.details
            }
        )

    return result


@router.get("/get_buyers_orders", response_model=List[OrderedGoodsFromBuyersData], status_code=status.HTTP_200_OK)
async def get_buyers_orders(
        date_from: datetime.date,
        date_to: datetime.date,
        service: OrderedGoodsFromBuyersService = Depends(get_ordered_goods_from_buyers_service)
):
    return await service.get_buyer_orders(date_from=date_from, date_to=date_to)


@router.post("/update_acceptance_status", response_model=OrderedGoodsFromBuyersResponse, status_code=status.HTTP_201_CREATED)
async def update_acceptance_status(
        data: List[IsAcceptanceStatus],
        service: OrderedGoodsFromBuyersService = Depends(get_ordered_goods_from_buyers_service)
):
    result = await service.update_acceptance_status(data)
    return result