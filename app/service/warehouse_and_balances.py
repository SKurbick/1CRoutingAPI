from typing import List

from app.models import DefectiveGoodsUpdate
from app.database.repositories import WarehouseAndBalancesRepository
from app.models.warehouse_and_balances import DefectiveGoodsResponse, Warehouse, CurrentBalances


class WarehouseAndBalancesService:
    def __init__(
            self,
            warehouse_and_balances_repository: WarehouseAndBalancesRepository,
    ):
        self.warehouse_and_balances_repository = warehouse_and_balances_repository

    async def add_defective_goods(self, data: List[DefectiveGoodsUpdate]) -> DefectiveGoodsResponse:
        result = await self.warehouse_and_balances_repository.add_defective_goods(data)
        return result

    async def get_warehouses(self) -> List[Warehouse]:
        result = await self.warehouse_and_balances_repository.get_warehouses()
        return result

    async def get_all_product_current_balances(self) -> List[CurrentBalances]:
        result = await self.warehouse_and_balances_repository.get_all_product_current_balances()
        return result