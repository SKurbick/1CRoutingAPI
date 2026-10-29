import datetime
from decimal import Decimal
from typing import Optional, List
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class FBOReservePatch(BaseModel):
    """Только бизнес-поля резерва ФБО; системные поля запрещены."""

    model_config = ConfigDict(extra="forbid")

    product_id: Optional[str] = Field(
        default=None, min_length=1, examples=["testwild"],
        description="ID существующего товара. null запрещён. Нельзя менять у резерва, связанного с перемещением.",
    )
    warehouse_id: Optional[int] = Field(
        default=None, gt=0, examples=[1],
        description="ID существующего склада. null запрещён. Нельзя менять у резерва, связанного с перемещением.",
    )
    ordered: Optional[Decimal] = Field(
        default=None, ge=0, allow_inf_nan=False, examples=[12],
        description="Новое полное количество резерва, не прибавка. Неотрицательное; допустимы дроби. null запрещён.",
    )
    account: Optional[str] = Field(
        default=None, examples=["Вектор"], description="Аккаунт продавца. null очищает значение.",
    )
    supply_id: Optional[str] = Field(
        default=None, examples=["WB-GI-166715280"], description="Номер поставки. null очищает значение.",
    )
    wb_warehouse: Optional[str] = Field(
        default=None, examples=["Коледино"], description="Название склада маркетплейса. null очищает значение.",
    )
    reserve_date: Optional[datetime.date] = Field(
        default=None, examples=["2026-10-26"], description="Дата резерва в формате YYYY-MM-DD. null очищает значение.",
    )
    expires_at: Optional[datetime.datetime] = Field(
        default=None, examples=["2026-11-01T12:00:00+03:00"],
        description="Срок действия: ISO 8601 с часовым поясом (Z или ±HH:MM). null очищает значение.",
    )

    @model_validator(mode="after")
    def validate_patch(self):
        if not self.model_fields_set:
            raise ValueError("Укажите хотя бы одно поле для изменения")
        for name in ("product_id", "warehouse_id", "ordered"):
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError(f"Поле {name} не может быть null")
        if self.expires_at is not None and self.expires_at.utcoffset() is None:
            raise ValueError("expires_at должен содержать часовой пояс")
        return self

example_shipment_of_goods_data = [
    {
        'author': 'admin',
        'supply_id': '1231231',
        'product_id': 'wild123',
        'warehouse_id': 1,
        'delivery_type': 'ФБО',
        'shipment_date': '2025-07-06',
        'wb_warehouse': 'Лентяево',
        'account': 'Хачатрян',
        'quantity': 12,
        "product_reserves_id": 11
    }
]


class DeliveryType(str, Enum):
    FBS = "ФБС"
    FBO = "ФБО"


class ShipmentOfGoodsResponse(BaseModel):
    status: int
    message: str
    details: Optional[str] = None
    data: Optional[List[dict]] = None


class ShipmentOfGoodsUpdate(BaseModel):
    author: str
    supply_id: str
    product_id: str
    warehouse_id: int
    delivery_type: str
    wb_warehouse: Optional[str] = None
    account: str
    quantity: int
    shipment_date: Optional[datetime.date] = None
    product_reserves_id: Optional[int] = None


class ShipmentParamsData(BaseModel):
    products: List[str]
    accounts: List[str]


class ReserveOfGoodsResponse(BaseModel):
    supply_id: Optional[str] = None
    product_reserves_id: Optional[int] = None


class ReserveOfGoodsCreate(BaseModel):
    product_id: str
    warehouse_id: int
    ordered: int
    account: str
    delivery_type: str
    wb_warehouse: Optional[str] = None
    reserve_date: datetime.date
    supply_id: str
    expires_at: datetime.datetime
    is_hanging: Optional[bool] = None


class ShippedGoods(BaseModel):
    supply_id: str
    quantity_shipped: int
    product_id:str


class ShippedGoodsByID(BaseModel):
    reserve_id: int
    quantity_shipped: int
    is_fulfilled: bool


example_shipped_goods_data = [
    {
        "supply_id": "WB-GI-166715280",
        "quantity_shipped": 5,
        "product_id": "wild123"
    }
]

example_reserve_of_goods_data = [
    {
        "product_id": "testwild",
        "warehouse_id": 1,
        "ordered": 20,
        "account": "Тоноян",
        "delivery_type": "ФБС",
        "wb_warehouse": "Писюлькино",
        "supply_id": "WB-GI-166715280",
        "reserve_date": "2025-07-25",
        "expires_at": "2025-08-05 16:08:57.089858",
    }
]

shipment_data_response_example = {

}


class ReservedData(BaseModel):
    reserve_id: int
    product_id: str
    warehouse_id: int
    ordered: int
    shipped: int
    account: str
    delivery_type: str
    wb_warehouse: Optional[str] = None
    supply_id: str
    reserve_date: datetime.date
    # created_at
    expires_at:Optional[datetime.datetime] = None
    is_fulfilled: bool
    is_hanging: Optional[bool] = None


data = [
    {
        "product_id": "wild123",
        "delivery_type_data": [
            {
                "reserve_type": "ФБО",
                "current_reserve": 12},
            {
                "reserve_type": "ФБО",
                "current_reserve": 12},
        ]

    }
]


class DeliveryTypeData(BaseModel):
    reserve_type: str
    current_reserve: int


class SummReserveData(BaseModel):
    product_id: str
    delivery_type_data: List[DeliveryTypeData]


class CreationWithMovement(ReserveOfGoodsCreate):
    move_from_supply: str
    quantity_to_move: int

class ShipmentWithReserveUpdating(ShipmentOfGoodsUpdate):
    is_fulfilled: bool

from pydantic import  field_validator

class WriteOffAccordingToFBS(ShipmentOfGoodsUpdate):
    assembly_tasks: List[int]

    @field_validator('quantity')
    def validate_quantity_equals_tasks_count(cls, v: int, info) -> int:
        """Проверяет, что quantity равно количеству assembly_tasks"""
        # Получаем значение assembly_tasks из данных
        assembly_tasks = info.data.get('assembly_tasks', [])

        if v != len(assembly_tasks):
            raise ValueError(
                f'Количество ({v}) должно быть равно количеству сборочных заданий({len(assembly_tasks)})'
            )
        return v
