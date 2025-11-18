from typing import List

from fastapi import APIRouter, Depends, status, Body, HTTPException, Query
from app.models.warehouse_and_balances import DefectiveGoodsUpdate, DefectiveGoodsResponse, example_defective_goods_data, Warehouse, CurrentBalances, \
    ValidStockData, example_assembly_metawild_data, AssemblyOrDisassemblyMetawildData, AssemblyMetawildResponse, assembly_or_disassembly_metawild_description, \
    add_defective_goods_description, ReSortingOperationResponse, ReSortingOperation, re_sorting_operations_description, example_re_sorting_operations, \
    AddStockByClient, AddStockByClientResponse, HistoricalStockData, HistoricalStockBody, StatusStats, ProductStats, WarehouseAndBalanceResponse, \
    ProductQuantityCheck, ProductQuantityCheckResult, product_quantity_check_description, product_quantity_check_response_description
from app.service.warehouse_and_balances import WarehouseAndBalancesService
from app.dependencies import get_warehouse_and_balances_service

router = APIRouter(prefix="/warehouse_and_balances", tags=["Склады и остатки"])


@router.get("/get_statuses_for_products_in_reserve", response_model=List[ProductStats] | WarehouseAndBalanceResponse, status_code=status.HTTP_200_OK)
async def get_statuses_for_products_in_reserve(
        service: WarehouseAndBalancesService = Depends(get_warehouse_and_balances_service)
):
    result = await service.get_statuses_for_products_in_reserve()
    return result


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
async def get_all_product_current_balances(
        service: WarehouseAndBalancesService = Depends(get_warehouse_and_balances_service)
):
    result = await service.get_all_product_current_balances()
    return result


# @router.get("/get_valid_stock_data", response_model=List[ValidStockData], status_code=status.HTTP_200_OK)
# async def get_valid_stock_data(
#         service: WarehouseAndBalancesService = Depends(get_warehouse_and_balances_service)
# ):
#     result = await service.get_valid_stock_data()
#     return result


@router.post("/assembly_or_disassembly_metawild", response_model=AssemblyMetawildResponse, status_code=status.HTTP_201_CREATED,
             description=assembly_or_disassembly_metawild_description)
async def assembly_or_disassembly_metawild(
        data: AssemblyOrDisassemblyMetawildData = Body(example=example_assembly_metawild_data),
        service: WarehouseAndBalancesService = Depends(get_warehouse_and_balances_service)
):
    result = await service.assembly_or_disassembly_metawild(data)

    if result.code_status >= 400:
        raise HTTPException(
            status_code=result.code_status,
            detail={
                "message": result.error_message,
                "details": "HTTPException"
            }
        )

    return result


@router.post("/re_sorting_operations", response_model=ReSortingOperationResponse, status_code=status.HTTP_201_CREATED,
             description=re_sorting_operations_description)
async def re_sorting_operations(
        data: ReSortingOperation = Body(example=example_re_sorting_operations),
        service: WarehouseAndBalancesService = Depends(get_warehouse_and_balances_service)
):
    result = await service.re_sorting_operations(data)

    if result.code_status >= 400:
        raise HTTPException(
            status_code=result.code_status,
            detail={
                "message": result.error_message,
                "details": "HTTPException"
            }
        )

    return result


@router.post("/add_stock_by_client", response_model=AddStockByClientResponse)
async def add_stock_by_client(
        data: List[AddStockByClient],
        service: WarehouseAndBalancesService = Depends(get_warehouse_and_balances_service)
):
    result = await service.add_stock_by_client(data)
    return result


@router.post("/get_historical_stocks", response_model=List[HistoricalStockData])
async def get_historical_stocks(
        data: HistoricalStockBody,
        service: WarehouseAndBalancesService = Depends(get_warehouse_and_balances_service)
):
    result = await service.get_historical_stocks(data)
    return result




@router.post("/product_quantity_check", response_model=ProductQuantityCheckResult,
             description=product_quantity_check_description, response_description=product_quantity_check_response_description)
async def product_quantity_check(
        data: List[ProductQuantityCheck],
        warehouse_id: int = Query(example=1, default=1, description="id Склада. По умолчанию 1"),
        service: WarehouseAndBalancesService = Depends(get_warehouse_and_balances_service)
):
    result = await service.product_quantity_check(warehouse_id=warehouse_id,data= data)
    return result
