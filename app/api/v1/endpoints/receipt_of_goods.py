from typing import List

from fastapi import APIRouter, Depends, status, Body, HTTPException
from app.dependencies import  get_receipt_of_goods_service
from app.models.receipt_of_goods import ReceiptOfGoodsResponse, example_receipt_of_goods_data, ReceiptOfGoodsUpdate, AddIncomingReceiptUpdate, example_add_incoming_receipt_data
from app.service.receipt_of_goods import ReceiptOfGoodsService

# router = APIRouter(prefix="receipt_of_goods",dependencies=[Depends(verify_service_token)])

router = APIRouter(prefix="/receipt_of_goods", tags=["Поступления товаров на склад продавца"])
"""
Алгоритм актуализации данных по поставкам:
1. Проверка по GUID: по совпадению из полученного списка изменяем валидность (is_valid) из True на False
2. Новые данные вставляем с is_valid = True
3. Для отображения поставок используем те, которые is_valid = True и event_status = Проведен 
"""


@router.post("/update", response_model=ReceiptOfGoodsResponse, status_code=status.HTTP_201_CREATED)
async def create_data(
        data: List[ReceiptOfGoodsUpdate],
# data: List[ReceiptOfGoodsUpdate] = Body(example=example_receipt_of_goods_data),
        service: ReceiptOfGoodsService = Depends(get_receipt_of_goods_service),
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

@router.post("/add_incoming_receipt", response_model=ReceiptOfGoodsResponse, status_code=status.HTTP_201_CREATED)
async def add_incoming_receipt(
        data: List[AddIncomingReceiptUpdate] = Body(example=example_add_incoming_receipt_data),
        service: ReceiptOfGoodsService = Depends(get_receipt_of_goods_service)
):
    """Оприходование товаров (от акта приемки) на основной склад продавца. Временное решение пока нет актуализации поступлений в 1С"""
    # result = await service.add_incoming_receipt(data)
    result = ReceiptOfGoodsResponse(status=201,message="стоит заглушка на оприходование")
    if result.status >= 400:
        raise HTTPException(
            status_code=result.status,
            detail={
                "message": result.message,
                "details": result.details
            }
        )

    return result