from typing import List

from fastapi import APIRouter, Depends, status, Body, HTTPException, Query
from app.models.shipment_of_goods import ShipmentOfGoodsUpdate, ShipmentOfGoodsResponse, example_shipment_of_goods_data, ShipmentParamsData, \
    ReserveOfGoodsResponse, ReserveOfGoodsCreate, example_reserve_of_goods_data, ShippedGoods, example_shipped_goods_data, DeliveryType
from app.service.shipment_of_goods import ShipmentOfGoodsService
from app.dependencies import get_shipment_of_goods_service

router = APIRouter(prefix="/shipment_of_goods", tags=["Отгрузка со склада продавца"])


@router.post("/update", response_model=ShipmentOfGoodsResponse, status_code=status.HTTP_201_CREATED)
async def create_data(
        delivery_type: DeliveryType = Query(..., description="принимает ФБС или ФБО"),
        data: List[ShipmentOfGoodsUpdate] = Body(example=example_shipment_of_goods_data),
        service: ShipmentOfGoodsService = Depends(get_shipment_of_goods_service)
):
    result = await service.create_data(data, delivery_type)

    if result.status >= 400:
        raise HTTPException(
            status_code=result.status,
            detail={
                "message": result.message,
                "details": result.details
            }
        )

    return result


@router.get("/get_shipment_params", response_model=ShipmentParamsData, status_code=status.HTTP_200_OK)
async def shipment_params_data(
        service: ShipmentOfGoodsService = Depends(get_shipment_of_goods_service)
):
    return await service.get_shipment_params()


@router.post("/create_reserve", response_model=List[ReserveOfGoodsResponse], status_code=status.HTTP_201_CREATED)
async def create_reserve(
        data: List[ReserveOfGoodsCreate] = Body(example=example_reserve_of_goods_data),
        service: ShipmentOfGoodsService = Depends(get_shipment_of_goods_service)
):
    result = await service.create_reserve(data)
    #
    # if result.status >= 400:
    #     raise HTTPException(
    #         status_code=result.status,
    #         detail={
    #             "message": result.message,
    #             "details": result.details
    #         }
    #     )

    return result


@router.post("/add_shipped_goods", response_model=List[ReserveOfGoodsResponse], status_code=status.HTTP_201_CREATED)
async def add_shipped_goods(
        data: List[ShippedGoods] = Body(example=example_shipped_goods_data),
        service: ShipmentOfGoodsService = Depends(get_shipment_of_goods_service)
):
    result = await service.add_shipped_goods(data)
    return result

# @router.get("/get_shipment_data", response_model=List[ITGroupData] | InventoryTransactionsResponse, status_code=status.HTTP_200_OK,
#             responses={200: shipment_data_response_example})
# async def get_shipment_data(
#         date_from: datetime.date = None,
#         date_to: datetime.date = None,
#         service: ShipmentOfGoodsService = Depends(get_shipment_of_goods_service)
# ):
#     if date_from is None or date_to is None:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="date_from and date_to are required."
#         )
#
#     return await service.get_shipment_data(date_from=date_from, date_to=date_to)
