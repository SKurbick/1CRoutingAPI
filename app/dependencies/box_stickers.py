from concurrent.futures import ProcessPoolExecutor

from fastapi import Depends, Request

from app.service.box_stickers import BoxStickerService


def get_process_pool(request: Request):
    return request.app.state.process_pool


def get_box_sticker_service(
        process_pool: ProcessPoolExecutor = Depends(get_process_pool),
) -> BoxStickerService:
    return BoxStickerService(process_pool=process_pool)
