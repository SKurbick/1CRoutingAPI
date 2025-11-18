from typing import Optional, Dict, List, Literal, Union

from pydantic import BaseModel, field_validator, Field, ConfigDict
from datetime import datetime, date








product_quantity_check_description = """
expected_physical_quantity - передайте что бы узнать "ожидаемый физический остаток"\n
expected_available_quantity -  передайте что бы узнать "ожидаемый свободный остаток"\n
product_id - обязательный параметр\n
так же нужно передать либо expected_physical_quantity либо expected_available_quantity\n
"""
product_quantity_check_response_description = """
если drawback = true - следовательно во вложенности есть ожидаемый остаток которого меньше фактического\n
enough =  true - значит соответствующего остатка достаточно\n
current_physical_quantity - ожидаемый физический остаток\n
 и expected_available_quantity - ожидаемый свободный остаток\n
"""

example_defective_goods_data = [
    {
        "author": "soskanerealka",
        "from_warehouse": 1,
        "to_warehouse": 2,
        "product_id": 'testwild',
        "status_id": 3,
        "quantity": 15,
        "correction_comment": "поломался пока чинил"
    }
]
assembly_or_disassembly_metawild_description = "Передавайте operation_type = 'assembly' если нужно собрать комплект из компонентов и operation_type = 'disassembly' если необходимо разобрать комплект на компоненты"
add_defective_goods_description = """
status_id = 1, при условии что товар переносится из брака в валидный остаток. status_id = 3, при условии что товар переносится
из валидного остатка в склад брака.
"""
re_sorting_operations_description = "Метод для операции пересортицы"
example_re_sorting_operations = {
    'from_product_id': "testwild",
    'to_product_id': "testwild2",
    'warehouse_id': 1,
    'quantity': 10,
    'reason': "Поставщик перепутал цвет товара",
    'author': "Зина"
}

example_assembly_metawild_data = {
    "metawild": "metawild_test",
    "count": 3,
    "author": "Ваня который соска",
    "warehouse_id": 1,
    "operation_type": "assembly"
}

from pydantic import model_validator


class ProductQuantityCheck(BaseModel):
    product_id: str
    expected_physical_quantity: Optional[int] = None
    expected_available_quantity: Optional[int] = None

    @model_validator(mode='after')
    def validate_at_least_one_quantity_field(self) -> 'ProductQuantityCheck':
        if (self.expected_physical_quantity is None and
                self.expected_available_quantity is None):
            raise ValueError(
                'Must provide either expected_physical_quantity or expected_available_quantity'
            )
        return self



class PhysicalQuantityCheck(BaseModel):
    current_physical_quantity: int
    enough: bool

class AvailableQuantityCheck(BaseModel):
    current_available_quantity: int
    enough: bool

class ProductCheckResult(BaseModel):
    product_id: str
    quantity_checks: List[Union[PhysicalQuantityCheck, AvailableQuantityCheck]]

class ProductQuantityCheckResult(BaseModel):
    drawback: bool  # один раз для всего ответа
    results: List[ProductCheckResult]  # список результатов по продуктам





class StockData(BaseModel):
    transaction_date: date
    end_of_day_balance: int

class HistoricalStockData(BaseModel):
    product_id: str
    data: List[StockData]



class HistoricalStockBody(BaseModel):
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    product_id: Optional[str] = None
    warehouse_id: int = Field(default=1, ge=1)
    page_size: int = Field(default=100, ge=1, le=5000)
    page_num: int = Field(default=1, ge=1)



class AssemblyMetawild(BaseModel):
    author: str
    warehouse_id: int
    metawild: str
    count: int


class AssemblyOrDisassemblyMetawildData(AssemblyMetawild):
    model_config = ConfigDict(extra='allow')
    operation_type: Literal["assembly", "disassembly"]  # только эти значения


class AssemblyMetawildResponse(BaseModel):
    product_id: str
    operation_status: str
    code_status: int
    error_message: Optional[str] = None


class DefectiveGoodsUpdate(BaseModel):
    author: str
    from_warehouse: int
    to_warehouse: int
    product_id: str
    status_id: int
    quantity: int
    correction_comment: Optional[str] = None



class DefectiveGoodsResponse(BaseModel):
    status: int
    message: str
    details: Optional[str] = None


class Warehouse(BaseModel):
    id: int
    name: str
    address: Optional[str] = None


class CurrentBalances(BaseModel):
    product_id: str
    warehouse_id: int
    reserved_quantity: int
    physical_quantity: int
    available_quantity: int


class ComponentsInfo(BaseModel):
    # {"required": 2, "available": 11, "component_id": "testwild"}
    required: int
    available: int
    component_id: str


class ValidStockData(BaseModel):
    product_id: str
    name: str
    is_kit: bool
    warehouse_id: int
    available_stock: int
    components_info: Optional[List[ComponentsInfo]] = None


class WarehouseAndBalanceResponse(BaseModel):
    status: int
    message: str
    details: Optional[str] = None


class ReSortingOperation(BaseModel):
    from_product_id: str
    to_product_id: str
    warehouse_id: int
    quantity: int
    reason: str
    author: str


class ReSortingOperationResponse(BaseModel):
    operation_status: str
    code_status: int
    error_message: Optional[str] = None


class AddStockByClient(BaseModel):
    product_id: str
    quantity: int
    warehouse_id: int
    author: str
    comment: str
    transaction_type: Literal['add_stock_by_client'] = 'add_stock_by_client'

class AddStockByClientResponse(BaseModel):
    status: int
    message: str
    details: Optional[str] = None


class StatusStats(BaseModel):
    fictitious_delivered: int
    in_hanging_supply: int
    in_technical_supply: int
    new: int
    total_count: int
    canceled_count: int
    actual_count: int

# Основная модель для продукта
class ProductStats(BaseModel):
    product_id: str  # local_vendor_code
    status_stats: StatusStats