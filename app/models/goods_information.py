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


class MetawildsData(BaseModel):
    id: str = Field(..., example="123e4567-e89b-12d3-a456-426614174000")
    name: str = Field(..., example="123e4567-e89b-12d3-a456-426614174000")
    kit_components: Dict[str, int] = Field(
        ...,
        example={
            "telescope": 1,
            "binoculars": 1,
            "field_guide": 1
        }
    )
    # class Config:
    #     schema_extra = {
    #         "example": {
    #             "id": "metawild",
    #             "name": "Губо-закаточная машинка",
    #             "kit_components": {"testwild": 2, "testwild2": 1}
    #         }
    #     }
