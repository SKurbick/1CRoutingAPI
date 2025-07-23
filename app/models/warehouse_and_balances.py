from typing import Optional, Dict, List, Literal

from pydantic import BaseModel, field_validator
from datetime import datetime

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
example_assembly_metawild_data = {
    "metawild": "metawild_test",
    "count": 3,
    "author": "Ваня который соска",
    "warehouse_id": 1,
    "operation_type": "assembly"
}


class AssemblyMetawild(BaseModel):
    author: str
    warehouse_id: int
    metawild: str
    count: int


class AssemblyOrDisassemblyMetawildData(AssemblyMetawild):
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
    physical_quantity: int


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
