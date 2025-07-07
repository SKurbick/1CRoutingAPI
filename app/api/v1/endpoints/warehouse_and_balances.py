from typing import List

from fastapi import APIRouter, Depends, status, Body, HTTPException
from app.models.warehouse_and_balances import DefectiveGoodsUpdate, DefectiveGoodsResponse, example_defective_goods_data, Warehouse, CurrentBalances
from app.service.warehouse_and_balances import WarehouseAndBalancesService
from app.dependencies import get_warehouse_and_balances_service

# router = APIRouter(prefix="/income_on_bank_account", dependencies=[Depends(verify_service_token)])
add_defective_goods_description = """
status_id = 1, при условии что товар переносится из брака в валидный остаток. status_id = 3, при условии что товар переносится
из валидного остатка в склад брака.
"""

router = APIRouter(prefix="/warehouse_and_balances", tags=["Склады и остатки"])


@router.post("/add_defective_goods", response_model=DefectiveGoodsResponse, status_code=status.HTTP_201_CREATED, description=add_defective_goods_description)
async def add_defective_goods(
        data: List[DefectiveGoodsUpdate] = Body(example=example_defective_goods_data),
        service: WarehouseAndBalancesService = Depends(get_warehouse_and_balances_service)
):
    result = await service.add_defective_goods(data)

    if result.status >= 400:
        raise HTTPException(
            status_code=result.status,
            detail={
                "message": result.message,
                "details": result.details
            }
        )

    return result


@router.get("/get_warehouses", response_model=List[Warehouse], status_code=status.HTTP_200_OK)
async def get_warehouses(
        service: WarehouseAndBalancesService = Depends(get_warehouse_and_balances_service)
):
    result = await service.get_warehouses()
    return result

@router.get("/get_all_product_current_balances", response_model=List[CurrentBalances], status_code=status.HTTP_200_OK)
async def get_warehouses(
        service: WarehouseAndBalancesService = Depends(get_warehouse_and_balances_service)
):
    result = await service.get_all_product_current_balances()
    return result