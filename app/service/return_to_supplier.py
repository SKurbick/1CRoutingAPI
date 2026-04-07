from typing import List

from app.database.repositories.return_to_supplier import ReturnToSupplierRepository
from app.models.return_to_supplier import ReturnToSupplierUpdate, ReturnToSupplierResponse


class ReturnToSupplierService:
    def __init__(self, repository: ReturnToSupplierRepository):
        self.repository = repository

    async def create_data(self, data: List[ReturnToSupplierUpdate]) -> ReturnToSupplierResponse:
        try:
            await self.repository.update_data(data)
            return ReturnToSupplierResponse(
                status="success",
                message=f"Обработано документов: {len(data)}"
            )
        except Exception as e:
            return ReturnToSupplierResponse(
                status="error",
                message="Ошибка при сохранении",
                details=str(e)
            )
