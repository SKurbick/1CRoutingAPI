from fastapi import APIRouter

from .endpoints import goods_information_router


router = APIRouter()

router.include_router(goods_information_router)


__all__ = [
    "router",
]
