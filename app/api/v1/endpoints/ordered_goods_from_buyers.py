import datetime
from typing import List
# OrderedGoodsFromBuyers
from fastapi import APIRouter, Depends, status, Body, HTTPException, Query

from app.models import UserPermissions
from app.models.ordered_goods_from_buyers import OrderedGoodsFromBuyersUpdate, OrderedGoodsFromBuyersResponse, example_ordered_goods_from_buyers_data, \
    IsAcceptanceStatus, OrderedGoodsAndPrintedBarcodeData, ordered_goods_and_printed_data_example
from app.service.ordered_goods_from_buyers import OrderedGoodsFromBuyersService
from app.dependencies import get_ordered_goods_from_buyers_service, get_info_from_token

# router = APIRouter(prefix="/income_on_bank_account", dependencies=[Depends(verify_service_token)])


router = APIRouter(prefix="/ordered_goods_from_buyers", tags=["Заказы товаров у поставщиков"])


@router.post("/update", response_model=OrderedGoodsFromBuyersResponse, status_code=status.HTTP_201_CREATED)
async def create_data(
        data: List[OrderedGoodsFromBuyersUpdate],
        # data: List[OrderedGoodsFromBuyersUpdate] = Body(example=example_ordered_goods_from_buyers_data),
        user: UserPermissions = Depends(get_info_from_token),
        service: OrderedGoodsFromBuyersService = Depends(get_ordered_goods_from_buyers_service),
):
    if not user.viewing:
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Permission Locked")
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


@router.get("/get_buyers_orders", response_model=OrderedGoodsAndPrintedBarcodeData, status_code=status.HTTP_200_OK)
async def get_buyers_orders(
        in_acceptance: bool = Query(description="Если передать параметр True, то параметры в date_from date_to будут проигнорированы"),
        date_from: datetime.date = None,
        date_to: datetime.date = None,
        user: UserPermissions = Depends(get_info_from_token),
        service: OrderedGoodsFromBuyersService = Depends(get_ordered_goods_from_buyers_service)
):
    if not user.viewing:
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Permission Locked")
    if not in_acceptance and (date_from is None or date_to is None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="date_from and date_to are required when in_acceptance is False"
        )
    return await service.get_buyer_orders(date_from=date_from, date_to=date_to, in_acceptance=in_acceptance)


@router.post("/update_acceptance_status", response_model=OrderedGoodsFromBuyersResponse, status_code=status.HTTP_201_CREATED)
async def update_acceptance_status(
        data: List[IsAcceptanceStatus],
        user: UserPermissions = Depends(get_info_from_token),
        service: OrderedGoodsFromBuyersService = Depends(get_ordered_goods_from_buyers_service)
):
    if not user.viewing:
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Permission Locked")
    result = await service.update_acceptance_status(data)
    return result
