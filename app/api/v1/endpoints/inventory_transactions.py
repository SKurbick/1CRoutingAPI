import datetime
from typing import List

from fastapi import APIRouter, Depends, status, Body, HTTPException

from app.models.inventory_transactions import ITGroupData, group_data_response_example, InventoryTransactionsResponse, AddStockByClientGroupData, \
    KitOperationsGroupData, IncomingReturnsGroupData, ReSortingOperationGroupData
from app.service.inventory_transactions import InventoryTransactionsService
from app.dependencies import get_inventory_transactions_service

router = APIRouter(prefix="/inventory_transactions", tags=["Перемещения товаров"])


@router.get("/group_data", response_model=List[ITGroupData] | InventoryTransactionsResponse, status_code=status.HTTP_200_OK,
            responses={200: group_data_response_example})
async def group_data(
        date_from: datetime.date = None,
        date_to: datetime.date = None,
        service: InventoryTransactionsService = Depends(get_inventory_transactions_service)
):
    if date_from is None or date_to is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="date_from and date_to are required."
        )

    return await service.group_data(date_from=date_from, date_to=date_to)


@router.get("/get_add_stock_by_client", response_model=List[AddStockByClientGroupData] | InventoryTransactionsResponse, status_code=status.HTTP_200_OK)
async def get_add_stock_by_client(date_from: datetime.date = None,
                                  date_to: datetime.date = None,
                                  service: InventoryTransactionsService = Depends(get_inventory_transactions_service)
                                  ):
    if date_from is None or date_to is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="date_from and date_to are required."
        )
    return await service.get_add_stock_by_client(date_from=date_from, date_to=date_to)


@router.get("/get_kit_operations", response_model=List[KitOperationsGroupData] | InventoryTransactionsResponse, status_code=status.HTTP_200_OK)
async def get_kit_operations(date_from: datetime.date = None,
                             date_to: datetime.date = None,
                             service: InventoryTransactionsService = Depends(get_inventory_transactions_service)
                             ):
    if date_from is None or date_to is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="date_from and date_to are required."
        )
    return await service.get_kit_operations(date_from=date_from, date_to=date_to)


@router.get("/get_incoming_returns", response_model=List[IncomingReturnsGroupData] | InventoryTransactionsResponse, status_code=status.HTTP_200_OK)
async def get_incoming_returns(date_from: datetime.date = None,
                               date_to: datetime.date = None,
                               service: InventoryTransactionsService = Depends(get_inventory_transactions_service)
                               ):
    if date_from is None or date_to is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="date_from and date_to are required."
        )
    return await service.get_incoming_returns(date_from=date_from, date_to=date_to)


@router.get("/get_re_sorting_operations", response_model=List[ReSortingOperationGroupData] | InventoryTransactionsResponse, status_code=status.HTTP_200_OK)
async def get_re_sorting_operations(date_from: datetime.date = None,
                                    date_to: datetime.date = None,
                                    service: InventoryTransactionsService = Depends(get_inventory_transactions_service)
                                    ):
    if date_from is None or date_to is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="date_from and date_to are required."
        )
    return await service.get_re_sorting_operations(date_from=date_from, date_to=date_to)
