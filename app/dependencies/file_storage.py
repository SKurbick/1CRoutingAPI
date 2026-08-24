from fastapi import Request

from app.file_storage import IFileStorage


def get_pool(request: Request) -> IFileStorage:
    """
    Получение файлового хранилища из состояния приложения.
    """
    return request.app.state.file_storage
