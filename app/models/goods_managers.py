from pydantic import BaseModel


all_goods_managers_example = {
    "description": "Список всех менеджеров товаров",
    "content": {
        "application/json": {
            "example": [
                {
                    "id": 1,
                    "name": "Петров А.В.",
                },
                {
                    "id": 2,
                    "name": "Сидоров А.Б.",
                },
            ]
        }
    },
}


class GoodsManager(BaseModel):
    id: int
    name: str
