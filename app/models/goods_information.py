from typing import Optional, Dict

from pydantic import BaseModel, field_validator
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
                    "kit_components": {"testwild": 2, "testwild2": 1}
                },
                {
                    "id": "wild1523",
                    "name": "Казан 20л черный (SB)",
                    "is_kit": False,
                    "share_of_kit": False,
                    "photo_link": None,
                    "kit_components": {}
                },
            ]
        }
    },
}


class MetawildsData(BaseModel):
    id: str
    name: str
    kit_components: Dict[str, int]


class AllProductsData(BaseModel):
    id: str
    name: str
    is_kit: bool
    share_of_kit: bool
    photo_link: Optional[str] = None
    kit_components: Optional[Dict[str, int]] = None
