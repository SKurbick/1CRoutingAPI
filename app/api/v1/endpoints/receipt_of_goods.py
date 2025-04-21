from typing import List

from fastapi import APIRouter, Depends, status, Body
from app.models.receipt_of_goods import ReceiptOfGoodsUpdate, ReceiptOfGoodsResponse, example_receipt_of_goods_data
from app.service.receipt_of_goods import ReceiptOfGoodsService
from app.dependencies import get_receipt_of_goods_service

# router = APIRouter(prefix="receipt_of_goods",dependencies=[Depends(verify_service_token)])

router = APIRouter(prefix="/receipt_of_goods")
"""
Алгоритм актуализации данных по поставкам:
1. Проверка по GUID: по совпадению из полученного списка изменяем валидность (is_valid) из True на False
2. Новые данные вставляем с is_valid = True
3. Для отображения поставок используем те, которые is_valid = True и event_status = Проведен 
"""


@router.post("/update", response_model=ReceiptOfGoodsResponse, status_code=status.HTTP_201_CREATED)
async def create_data(
        data: List[ReceiptOfGoodsUpdate] = Body(example=example_receipt_of_goods_data),
        service: ReceiptOfGoodsService = Depends(get_receipt_of_goods_service)
):
    try:
        response = await service.create_data(data)
        return {"status": 201, "message": "Успешно"}
    except Exception as e:
        return
