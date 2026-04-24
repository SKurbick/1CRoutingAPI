

from app.database.repositories.sticker_generation_tasks import StickerGenerationTasksRepository
from app.service.localisation import LocalisationService
from app.service.sticker_user_data import StickerUserDataService


class StickerGenerationService:
    def __init__(
        self,
        generation_tasks_repo: StickerGenerationTasksRepository,
        user_data_service: StickerUserDataService,
        localisation_service: LocalisationService,
        publisher: str, # TODO: примочка для брокера
    ):
        self.generation_tasks_repo = generation_tasks_repo
        self.user_data_service = user_data_service
        self.localisation_service = localisation_service
        self.publisher = publisher