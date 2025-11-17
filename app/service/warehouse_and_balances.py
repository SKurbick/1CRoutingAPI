from pprint import pprint
from typing import List

from app.dependencies.config import settings
from app.infrastructure.ONE_C import ONECRouting
from app.models import DefectiveGoodsUpdate, AddStockByClientResponse, StatusStats
from app.database.repositories import WarehouseAndBalancesRepository
from app.models.warehouse_and_balances import DefectiveGoodsResponse, Warehouse, CurrentBalances, ValidStockData, AssemblyOrDisassemblyMetawildData, \
    AssemblyMetawildResponse, ReSortingOperation, ReSortingOperationResponse, AddStockByClient, HistoricalStockBody, HistoricalStockData, ProductStats, \
    WarehouseAndBalanceResponse, ProductQuantityCheckResult, ProductQuantityCheck, PhysicalQuantityCheck, AvailableQuantityCheck, \
    ProductCheckResult


class WarehouseAndBalancesService:
    def __init__(
            self,
            warehouse_and_balances_repository: WarehouseAndBalancesRepository,
    ):
        self.warehouse_and_balances_repository = warehouse_and_balances_repository

    async def get_statuses_for_products_in_reserve(self) -> List[ProductStats]| WarehouseAndBalanceResponse:
        result = await self.warehouse_and_balances_repository.get_statuses_for_products_in_reserve()
        return result

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


    async def product_quantity_check(self, warehouse_id: int, data: List[ProductQuantityCheck]) -> ProductQuantityCheckResult:
        all_product_current_balances = await self.get_all_product_current_balances()

        results = []
        overall_drawback = False

        for check_request in data:
            # Фильтруем балансы по product_id и warehouse_id = 1
            product_balances = [
                b for b in all_product_current_balances
                if b.product_id == check_request.product_id and b.warehouse_id == warehouse_id
            ]

            quantity_checks = []
            product_drawback = False

            if not product_balances:
                # Если нет данных по складу 1, считаем что количества недостаточно
                if check_request.expected_physical_quantity is not None:
                    quantity_checks.append(PhysicalQuantityCheck(
                        current_physical_quantity=0,
                        enough=False
                    ))
                    product_drawback = True
                if check_request.expected_available_quantity is not None:
                    quantity_checks.append(AvailableQuantityCheck(
                        current_available_quantity=0,
                        enough=False
                    ))
                    product_drawback = True
            else:
                # Берем первый подходящий баланс (warehouse_id = 1)
                balance = product_balances[0]

                # Проверяем physical quantity
                if check_request.expected_physical_quantity is not None:
                    physical_enough = check_request.expected_physical_quantity <= balance.physical_quantity
                    if not physical_enough:
                        product_drawback = True
                    quantity_checks.append(PhysicalQuantityCheck(
                        current_physical_quantity=balance.physical_quantity,
                        enough=physical_enough
                    ))

                # Проверяем available quantity
                if check_request.expected_available_quantity is not None:
                    available_enough = check_request.expected_available_quantity <= balance.available_quantity
                    if not available_enough:
                        product_drawback = True
                    quantity_checks.append(AvailableQuantityCheck(
                        current_available_quantity=balance.available_quantity,
                        enough=available_enough
                    ))

            # Обновляем общий drawback
            if product_drawback:
                overall_drawback = True

            results.append(ProductCheckResult(
                product_id=check_request.product_id,
                quantity_checks=quantity_checks
            ))

        return ProductQuantityCheckResult(
            drawback=overall_drawback,
            results=results
        )
