from pprint import pprint
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

    async def get_historical_stocks(self, data: HistoricalStockBody) -> List[HistoricalStockData]:
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

        if result.code_status == 201:
            kit_components = await self.warehouse_and_balances_repository.kit_components_by_product_id(data.metawild)

            data.kit_komponents = kit_components

            refactor_kit_components = self.refactor_kit_components(data.model_dump(exclude={"warehouse_id"}))
            pprint(refactor_kit_components)
            one_c_connect = ONECRouting(base_url=settings.ONE_C_BASE_URL, password=settings.ONE_C_PASSWORD, login=settings.ONE_C_LOGIN)
            await one_c_connect.assembly_or_disassembly_metawild(data=refactor_kit_components)


        return result

    @staticmethod
    def refactor_kit_components(data):
        """
        Преобразует содержимое kit_komponents в список словарей,
        где каждый словарь содержит product_id и quantity
        """
        # Создаем копию исходных данных, чтобы не изменять оригинал
        result = data.copy()

        # Преобразуем kit_komponents в список словарей
        if 'kit_komponents' in result and isinstance(result['kit_komponents'], dict):
            kit_components_list = []
            for product_id, quantity in result['kit_komponents'].items():
                kit_components_list.append({
                    'product_id': product_id,
                    'quantity': quantity
                })
            result['kit_komponents'] = kit_components_list

        return result

    async def re_sorting_operations(self, data: ReSortingOperation) -> ReSortingOperationResponse:
        result = await self.warehouse_and_balances_repository.re_sorting_operations(data)
        if result.code_status == 201:
            one_c_connect = ONECRouting(base_url=settings.ONE_C_BASE_URL, password=settings.ONE_C_PASSWORD, login=settings.ONE_C_LOGIN)
            await one_c_connect.re_sorting_operations(data=data)
        return result

    async def add_stock_by_client(self, data: List[AddStockByClient]) -> AddStockByClientResponse:
        result = await self.warehouse_and_balances_repository.add_stock_by_client(data)
        return result
