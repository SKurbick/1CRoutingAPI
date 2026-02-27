from concurrent.futures import ProcessPoolExecutor

from fastapi import Depends, Request
from asyncpg import Pool

from app.database.repositories.box_stickers_templates import BoxStickersTemplateRepository
from app.service.box_stickers import BoxStickerService
from .goods_information import get_goods_information_service, GoodsInformationService


def get_pool(request: Request) -> Pool:
    """Получение пула соединений из состояния приложения."""
    return request.app.state.pool


def get_process_pool(request: Request):
    """Получения пула процессов из состояния приложения."""
    return request.app.state.process_pool


def get_box_stickers_templates_repo(
        pool: Pool = Depends(get_pool),
) -> BoxStickersTemplateRepository:
    return BoxStickersTemplateRepository(pool)


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
