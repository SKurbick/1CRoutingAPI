from concurrent.futures import ProcessPoolExecutor

from fastapi import Depends, Request
from asyncpg import Pool

from app.database.repositories.box_stickers_templates import BoxStickersTemplateRepository
from app.database.repositories.localisation import LocalisationRepository
from app.database.repositories.sticker_generation_tasks import StickerGenerationTasksRepository
from app.database.repositories.sticker_user_data import StickerUserDataRepository
from app.database.repositories.stickers_storage import StickersStorageRepository
from app.file_storage.base.interface import IFileStorage
from app.service.box_stickers import BoxStickerService, StickerTemplateBuilderService
from app.service.localisation import LocalisationService
from app.service.sticker_generation_publisher import StickerGenerationPublisher
from app.service.sticker_generation_service import StickerGenerationService
from app.service.sticker_template_save import StickerTemplateSaveService
from app.service.sticker_user_data import StickerUserDataService
from .goods_information import get_goods_information_service, GoodsInformationService


def get_pool(request: Request) -> Pool:
    """Получение пула соединений из состояния приложения."""
    return request.app.state.pool


def get_process_pool(request: Request):
    """Получения пула процессов из состояния приложения."""
    return request.app.state.process_pool


# def get_box_stickers_templates_repo(
#         pool: Pool = Depends(get_pool),
# ) -> BoxStickersTemplateRepository:
#     return BoxStickersTemplateRepository(pool)

def get_box_stickers_templates_repo(
        pool: Pool = Depends(get_pool),
) -> StickersStorageRepository:
    return StickersStorageRepository(pool)

def get_localisation_repo(
        pool: Pool = Depends(get_pool),
) -> LocalisationRepository:
    return LocalisationRepository(pool)

def get_user_data_repo(
        pool: Pool = Depends(get_pool),
) -> StickerUserDataRepository:
    return StickerUserDataRepository(pool)

def get_sticker_user_data_repo(
    pool: Pool = Depends(get_pool),
) -> StickerUserDataRepository:
    return StickerUserDataRepository(pool)


def get_box_sticker_service(
        process_pool: ProcessPoolExecutor = Depends(get_process_pool),
        template_repo: BoxStickersTemplateRepository = Depends(get_box_stickers_templates_repo),
        goods_info_service: GoodsInformationService = Depends(get_goods_information_service),
) -> BoxStickerService:
    return BoxStickerService(
        process_pool=process_pool,
        template_repo=template_repo,
        goods_info_service=goods_info_service,
    )

def get_box_sticker_service_1(
        products_repo: StickersStorageRepository = Depends(get_box_stickers_templates_repo),
        localisation_repo: LocalisationRepository = Depends(get_localisation_repo),
        user_data_repo: StickerUserDataRepository = Depends(get_user_data_repo)
) -> StickerTemplateBuilderService:
    return StickerTemplateBuilderService(
        products_repo=products_repo,
        localisation_repo=localisation_repo,
        user_data_repo=user_data_repo
    )

def get_sticker_user_data_service(
        repo: StickerUserDataRepository = Depends(get_sticker_user_data_repo),
) -> StickerUserDataService:
    return StickerUserDataService(repo)

def get_localisation_service(
        repo: LocalisationRepository = Depends(get_localisation_repo)
) -> LocalisationService:
    return LocalisationService(repo)

def get_sticker_template_save_service(
    user_data_service: StickerUserDataService = Depends(get_sticker_user_data_service),
    localisation_service: LocalisationService = Depends(get_localisation_service),
) -> StickerTemplateSaveService:
    return StickerTemplateSaveService(
        user_data_service=user_data_service,
        localisation_service=localisation_service,
    )

def get_sticker_generation_tasks_repo(
    pool: Pool = Depends(get_pool),
) -> StickerGenerationTasksRepository:
    return StickerGenerationTasksRepository(pool)


def get_sticker_generation_publisher() -> StickerGenerationPublisher:
    return StickerGenerationPublisher()

def get_file_storage(request: Request) -> IFileStorage:
    """
    Берет уже инициализированное хранилище из состояния приложения.
    """
    return request.app.state.file_storage

def get_sticker_generation_service(
    generation_tasks_repo: StickerGenerationTasksRepository = Depends(
        get_sticker_generation_tasks_repo),
    user_data_service: StickerUserDataService = Depends(
        get_sticker_user_data_service),
    localisation_service: LocalisationService = Depends(
        get_localisation_service),
    publisher: StickerGenerationPublisher = Depends(
        get_sticker_generation_publisher),
    file_storage: IFileStorage = Depends(get_file_storage)

    
) -> StickerGenerationService:
    return StickerGenerationService(
        generation_tasks_repo=generation_tasks_repo,
        user_data_service=user_data_service,
        localisation_service=localisation_service,
        publisher=publisher,
        file_storage=file_storage)