import datetime
from typing import List

from fastapi import APIRouter, Depends, status, Body, HTTPException

from app.models import UserPermissions
from app.models.inventory_check import InventoryCheckUpdate, InventoryCheckResponse, example_inventory_check_data, InventoryData, InventoryDataResponse, \
    inventory_data_response_example, IDGroupData
from app.service.inventory_check import InventoryCheckService
from app.dependencies import get_inventory_check_service, get_info_from_token

router = APIRouter(prefix="/inventory_check", tags=["Инвентаризация"])


@router.post("/add_inventory_result", response_model=InventoryCheckResponse, status_code=status.HTTP_201_CREATED)
async def create_data(
        data: InventoryCheckUpdate = Body(example=example_inventory_check_data),
        user: UserPermissions = Depends(get_info_from_token),
        service: InventoryCheckService = Depends(get_inventory_check_service)
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


@router.get("/get_inventory_data", response_model=List[IDGroupData] | InventoryDataResponse, status_code=status.HTTP_200_OK,
            responses={200: inventory_data_response_example})
async def get_inventory_data(
        date_from: datetime.date = None,
        date_to: datetime.date = None,
        user: UserPermissions = Depends(get_info_from_token),
        service: InventoryCheckService = Depends(get_inventory_check_service)
):
    if not user.viewing:
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Permission Locked")
    if date_from is None or date_to is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="date_from and date_to are required."
        )

    return await service.get_inventory_data(date_from=date_from, date_to=date_to)
