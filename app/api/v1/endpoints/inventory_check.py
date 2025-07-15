from typing import List

from fastapi import APIRouter, Depends, status, Body, HTTPException
from app.models.inventory_check import InventoryCheckUpdate, InventoryCheckResponse, example_inventory_check_data
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
