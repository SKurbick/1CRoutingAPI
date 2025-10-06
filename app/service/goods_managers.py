from app.database.repositories.goods_managers import GoodsManagerRepository
from app.models.goods_managers import GoodsManager


class GoodsManagersService:
    def __init__(self, repository: GoodsManagerRepository):
        self.repository = repository

    async def get_all_managers(self) -> list[GoodsManager]:
        return await self.repository.get_all_managers()
