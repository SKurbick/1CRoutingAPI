from typing import List

from fastapi import APIRouter, Depends, status, Body, HTTPException
from app.models.shipment_of_goods import ShipmentOfGoodsUpdate, ShipmentOfGoodsResponse, example_shipment_of_goods_data
from app.service.shipment_of_goods import ShipmentOfGoodsService
from app.dependencies import get_shipment_of_goods_service

router = APIRouter(prefix="/shipment_of_goods")


@router.post("/update", response_model=ShipmentOfGoodsResponse, status_code=status.HTTP_201_CREATED)
async def create_data(
        data: List[ShipmentOfGoodsUpdate] = Body(example=example_shipment_of_goods_data),
        service: ShipmentOfGoodsService = Depends(get_shipment_of_goods_service)
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
