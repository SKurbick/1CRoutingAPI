from typing import Optional, Dict

from pydantic import BaseModel, ConfigDict
from datetime import datetime

from pydantic.v1 import Field

metawilds_data_example = {
    "description": "Список меетавилдов/наборов с его компонентами ",
    "content": {
        "application/json": {
            "example": [
                {
                    "id": "metawild",
                    "name": "Губо-закаточная машинка",
                    "kit_components": {"testwild": 2, "testwild2": 1}
                }
            ]
        }
    },
}
all_products_data_example = {
    "description": "Список всех активных товаров, включая и наборы ",
    "content": {
        "application/json": {
            "example": [
                {
                    "id": "some_wild",
                    "name": "Губо-закаточная машинка",
                    "photo_link": "https://histrf.ru/images/common/19/RJ1SavyfUXRPzURBLqpSqmryu8mP1jl08kYToYWd.jpg",
                    "is_kit": True,
                    "share_of_kit": False,
                    "kit_components": {"testwild": 2, "testwild2": 1},
                    "length": 20,
                    "width": 30,
                    "height": 15,
                    "manager": "Арсеньев Ф.А."
                },
                {
                    "id": "wild1523",
                    "name": "Казан 20л черный (SB)",
                    "is_kit": False,
                    "share_of_kit": False,
                    "photo_link": None,
                    "kit_components": {},
                    "length": None,
                    "width": None,
                    "height": None,
                    "manager": None
                },
            ]
        }
    },
}



class MetawildsData(BaseModel):
    id: str
    name: str
    kit_components: Dict[str, int]


class ProductBase(BaseModel):
    name: str
    is_kit: bool
    share_of_kit: bool
    photo_link: Optional[str] = None
    kit_components: Optional[Dict[str, int]] = None


class AllProductsData(ProductBase):
    id: str
    length: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    manager: Optional[str] = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(ProductBase):
    name: Optional[str] = None
    is_kit: Optional[bool] = None
    share_of_kit: Optional[bool] = None


class GoodsResponse(BaseModel):
    status: int
    message: str
    details: Optional[str] = None


class ProductInfo(BaseModel):
    id: str
    length: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    manager: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": "wild1234",
                    "length": 25,
                    "width": 80,
                    "height": 16,
                    "manager": "Артём Валенкин",
                },
            ]
        }
    )
