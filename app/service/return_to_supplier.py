from typing import List

from app.database.repositories.return_to_supplier import ReturnToSupplierRepository
from app.models.return_to_supplier import ReturnToSupplierUpdate, ReturnToSupplierResponse


class ReturnToSupplierService:
    def __init__(self, repository: ReturnToSupplierRepository):
        self.repository = repository

    async def create_data(self, data: List[ReturnToSupplierUpdate]) -> ReturnToSupplierResponse:
        return await self.repository.update_data(data)
