
from typing import List, Optional
from pydantic import BaseModel

class Order(BaseModel):
    sum: int
    count: int

class Wild(BaseModel):
    wild_code: str
    orders: List[Order]

class SupplyData(BaseModel):
    supply_id: str
    wilds: List[Wild]

class AccountData(BaseModel):
    account: str
    inn: str
    data: List[SupplyData]

# Пример использования:
input_data_example= {
    "account": "Хачатрян",
    "inn": "771675966776",
    "data": [
        {
            "supply_id": "170261889",
            "wilds": [
                {
                    "wild_code": "wild128",
                    "orders": [
                        {
                            "sum": 0,
                            "count": 1
                        }
                    ]
                }
            ]
        }
    ]
}
