from fastapi import APIRouter, Depends, status

from app.dependencies import get_goods_managers_service
from app.models.goods_managers import all_goods_managers_example, GoodsManager
from app.service.goods_managers import GoodsManagersService


router = APIRouter(prefix="/goods_managers", tags=["Информация о менеджерах товаров"])


@router.get(
        "/get_all_managers", 
        response_model=list[GoodsManager], 
        status_code=status.HTTP_200_OK,
        responses={200: all_goods_managers_example})
async def get_all_managers(
        service: GoodsManagersService = Depends(get_goods_managers_service)
):
    return await service.get_all_managers()
