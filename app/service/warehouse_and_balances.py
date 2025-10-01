from typing import List

from app.dependencies.config import settings
from app.infrastructure.ONE_C import ONECRouting
from app.models import DefectiveGoodsUpdate, AddStockByClientResponse
from app.database.repositories import WarehouseAndBalancesRepository
from app.models.warehouse_and_balances import DefectiveGoodsResponse, Warehouse, CurrentBalances, ValidStockData, AssemblyOrDisassemblyMetawildData, \
    AssemblyMetawildResponse, ReSortingOperation, ReSortingOperationResponse, AddStockByClient, HistoricalStockBody, HistoricalStockData


class WarehouseAndBalancesService:
    def __init__(
            self,
            warehouse_and_balances_repository: WarehouseAndBalancesRepository,
    ):
        self.warehouse_and_balances_repository = warehouse_and_balances_repository

    async def get_historical_stocks(self, data:HistoricalStockBody) -> List[HistoricalStockData]:
        result = await self.warehouse_and_balances_repository.get_historical_stocks(data)
        return result


    async def add_defective_goods(self, data: List[DefectiveGoodsUpdate]) -> DefectiveGoodsResponse:
        result = await self.warehouse_and_balances_repository.add_defective_goods(data)
        return result

    async def get_warehouses(self) -> List[Warehouse]:
        result = await self.warehouse_and_balances_repository.get_warehouses()
        return result

    async def get_all_product_current_balances(self) -> List[CurrentBalances]:
        result = await self.warehouse_and_balances_repository.get_all_product_current_balances()
        return result

    async def get_valid_stock_data(self) -> List[ValidStockData]:
        result = await self.warehouse_and_balances_repository.get_valid_stock_data()
        return result

    async def assembly_or_disassembly_metawild(self, data: AssemblyOrDisassemblyMetawildData) -> AssemblyMetawildResponse:
        result = await self.warehouse_and_balances_repository.assembly_or_disassembly_metawild(data)
        return result

    async def re_sorting_operations(self, data: ReSortingOperation) -> ReSortingOperationResponse:
        result = await self.warehouse_and_balances_repository.re_sorting_operations(data)
        if result.code_status == 201:
            one_c_connect = ONECRouting(base_url=settings.ONE_C_BASE_URL, password=settings.ONE_C_PASSWORD, login=settings.ONE_C_LOGIN)
            await one_c_connect.re_sorting_operations(data=data)
        return result



    async def add_stock_by_client(self,data: List[AddStockByClient]) -> AddStockByClientResponse:
        result = await self.warehouse_and_balances_repository.add_stock_by_client(data)
        return result