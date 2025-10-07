import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, status, Body, HTTPException, Query

from app.models import ShippedGoodsByID
from app.models.shipment_of_goods import ShipmentOfGoodsUpdate, ShipmentOfGoodsResponse, example_shipment_of_goods_data, ShipmentParamsData, \
    ReserveOfGoodsResponse, ReserveOfGoodsCreate, example_reserve_of_goods_data, ShippedGoods, example_shipped_goods_data, DeliveryType, ReservedData, \
    SummReserveData, CreationWithMovement
from app.service.shipment_of_goods import ShipmentOfGoodsService
from app.dependencies import get_shipment_of_goods_service

router = APIRouter(prefix="/shipment_of_goods", tags=["Отгрузка со склада продавца"])



@router.post("/creation_reserve_with_movement", response_model=ShipmentOfGoodsResponse, status_code=status.HTTP_201_CREATED)
async def creation_reserve_with_movement(
        data: List[CreationWithMovement],
        delivery_type: DeliveryType = Query(..., description="принимает ФБС или ФБО"),
        service: ShipmentOfGoodsService = Depends(get_shipment_of_goods_service)
):
    """Создание поставки резерва с перемещением из другой поставки резерва.\n
    Для осуществления перемещения товара необходимо, чтобы исходная поставка (move_from_supply) с соответствующим product_id была создана заранее.
    \n quantity_to_move - какое количество
    \n move_from_supply - из какой поставки """
    result = await service.creation_reserve_with_movement(data, delivery_type)
    return result


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
        data: List[ReserveOfGoodsCreate], #= Body(example=example_reserve_of_goods_data)
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


@router.get("/get_reserved_data", response_model=List[ReservedData], status_code=status.HTTP_200_OK)
async def get_reserved_data(
        service: ShipmentOfGoodsService = Depends(get_shipment_of_goods_service),
        delivery_type: DeliveryType = Query(None, description="принимает ФБС или ФБО"),
        is_fulfilled: Optional[bool] = Query(None, description="Фильтр по статусу отгрузок. False для неотгруженных"),
        begin_date: Optional[datetime.date] = Query(None, description="Начальная дата"),
):
    return await service.get_reserved_data(is_fulfilled, begin_date, delivery_type)


@router.post("/add_shipped_goods_by_id", response_model=ShipmentOfGoodsResponse, status_code=status.HTTP_201_CREATED)
async def add_shipped_goods_by_id(
        data: List[ShippedGoodsByID],
        service: ShipmentOfGoodsService = Depends(get_shipment_of_goods_service)
):
    result = await service.add_shipped_goods_by_id(data)
    return result


@router.post("/add_shipped_goods", response_model=List[ReserveOfGoodsResponse], status_code=status.HTTP_201_CREATED)
async def add_shipped_goods(
        data: List[ShippedGoods] = Body(example=example_shipped_goods_data),
        service: ShipmentOfGoodsService = Depends(get_shipment_of_goods_service)
):
    result = await service.add_shipped_goods(data)
    return result


@router.get("/summ_reserve_data", response_model=List[SummReserveData], status_code=status.HTTP_200_OK)
async def get_summ_reserve_data(
        service: ShipmentOfGoodsService = Depends(get_shipment_of_goods_service)
):
    result = await service.get_summ_reserve_data()
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
