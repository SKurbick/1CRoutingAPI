

from app.database.repositories.importers import ImporterRepository
from app.models.box_stickers import ImporterView


class ImporterService:

    def __init__(self,
                 importer_repo: ImporterRepository):
        self.importer_repo = importer_repo
    

    async def get_list_importers(self) -> list[ImporterView]:
        """Получить список импортеров"""

        return await self.importer_repo.get_all()