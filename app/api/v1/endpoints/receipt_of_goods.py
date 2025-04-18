from typing import List

from fastapi import APIRouter, Depends, status, Body
from app.models.receipt_of_goods import ReceiptOfGoodsUpdate, ReceiptOfGoodsResponse, example_receipt_of_goods_data
from app.service.receipt_of_goods import ReceiptOfGoodsService
from app.dependencies import get_receipt_of_goods_service

# router = APIRouter(prefix="receipt_of_goods",dependencies=[Depends(verify_service_token)])

router = APIRouter(prefix="/receipt_of_goods")


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

