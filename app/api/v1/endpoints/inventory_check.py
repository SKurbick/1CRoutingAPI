import datetime
from typing import List

from fastapi import APIRouter, Depends, status, Body, HTTPException
from app.models.inventory_check import InventoryCheckUpdate, InventoryCheckResponse, example_inventory_check_data, InventoryData, InventoryDataResponse, \
    inventory_data_response_example, IDGroupData
from app.service.inventory_check import InventoryCheckService
from app.dependencies import get_inventory_check_service

router = APIRouter(prefix="/inventory_check", tags=["Инвентаризация"])


@router.post("/add_inventory_result", response_model=InventoryCheckResponse, status_code=status.HTTP_201_CREATED)
async def create_data(
        data: InventoryCheckUpdate = Body(example=example_inventory_check_data),
        service: InventoryCheckService = Depends(get_inventory_check_service)
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


@router.get("/get_inventory_data", response_model=List[IDGroupData] | InventoryDataResponse, status_code=status.HTTP_200_OK,
            responses={200: inventory_data_response_example})
async def get_inventory_data(
        date_from: datetime.date = None,
        date_to: datetime.date = None,
        service: InventoryCheckService = Depends(get_inventory_check_service)
):
    if date_from is None or date_to is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="date_from and date_to are required."
        )

    return await service.get_inventory_data(date_from=date_from, date_to=date_to)
