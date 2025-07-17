import datetime
from pprint import pprint
from typing import List

from app.models import OrderedGoodsFromBuyersUpdate
from app.database.repositories import InventoryTransactionsRepository
from app.models.inventory_transactions import ITGroupData


class InventoryTransactionsService:
    def __init__(
            self,
            inventory_transactions_repository: InventoryTransactionsRepository,
    ):
        self.inventory_transactions_repository = inventory_transactions_repository

    async def group_data(self, date_from: datetime.date, date_to: datetime.date) -> List[ITGroupData]:
        group_data = await self.inventory_transactions_repository.group_data(date_from=date_from, date_to=date_to)
        return group_data
