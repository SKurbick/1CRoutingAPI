import datetime
from typing import List

from app.models import InventoryCheckUpdate
from app.database.repositories import InventoryCheckRepository
from app.models.inventory_check import InventoryCheckResponse, InventoryData


class InventoryCheckService:
    def __init__(
            self,
            inventory_check_repository: InventoryCheckRepository,
    ):
        self.inventory_check_repository = inventory_check_repository

    async def create_data(self, data: InventoryCheckUpdate) -> InventoryCheckResponse:
        result = await self.inventory_check_repository.update_data(data)
        return result


    async def get_inventory_data(self, date_from:datetime.date, date_to:datetime.date) -> List[InventoryData]:
        result = await self.inventory_check_repository.get_inventory_data(date_from = date_from, date_to = date_to)
        return result