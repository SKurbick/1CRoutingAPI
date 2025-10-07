import datetime
from pprint import pprint
from typing import List

from app.models import OrderedGoodsFromBuyersUpdate
from app.database.repositories import InventoryTransactionsRepository
from app.models.inventory_transactions import ITGroupData, AddStockByClientGroupData, KitOperationsGroupData, IncomingReturnsGroupData, \
    ReSortingOperationGroupData


class InventoryTransactionsService:
    def __init__(
            self,
            inventory_transactions_repository: InventoryTransactionsRepository,
    ):
        self.inventory_transactions_repository = inventory_transactions_repository


    async def get_re_sorting_operations(self, date_from: datetime.date, date_to: datetime.date) -> List[ReSortingOperationGroupData]:
        data = await self.inventory_transactions_repository.get_re_sorting_operations(date_from=date_from, date_to=date_to)
        return data


    async def get_incoming_returns(self, date_from: datetime.date, date_to: datetime.date) -> List[IncomingReturnsGroupData]:
        data = await self.inventory_transactions_repository.get_incoming_returns(date_from=date_from, date_to=date_to)
        return data


    async def get_kit_operations(self, date_from: datetime.date, date_to: datetime.date) -> List[KitOperationsGroupData]:
        data = await self.inventory_transactions_repository.get_kit_operations(date_from=date_from, date_to=date_to)
        return data


    async def get_add_stock_by_client(self, date_from: datetime.date, date_to: datetime.date) -> List[AddStockByClientGroupData]:
        data = await self.inventory_transactions_repository.get_add_stock_by_client(date_from=date_from, date_to=date_to)
        return data

    async def group_data(self, date_from: datetime.date, date_to: datetime.date) -> List[ITGroupData]:
        group_data = await self.inventory_transactions_repository.group_data(date_from=date_from, date_to=date_to)
        return group_data
