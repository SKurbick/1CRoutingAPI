from abc import ABC, abstractmethod
from typing import AsyncIterable, BinaryIO

from .constants import DEFAULT_CHUNK_SIZE, DEFAULT_EXPIRES_IN


class IFileStorage(ABC):
    """
    Интерфейс файлового хранилища.
    Бакет/контейнер задаётся при инициализации конкретной реализации.
    """

    @abstractmethod
    async def upload(
        self,
        file_key: str,
        data: bytes | BinaryIO | AsyncIterable[bytes],
        content_type: str | None = None,
        metadata: dict[str, str] | None = None,
        **provider_kwargs,
    ) -> str:
        """
        Загрузить файл. Возвращает `file_key` или публичный URL.
        """

    @abstractmethod
    async def download(
        self,
        file_key: str,
        **provider_kwargs,
    ) -> bytes:
        """
        Скачать файл целиком. Для больших файлов используйте `download_stream`.
        """

    @abstractmethod
    async def download_stream(
        self,
        file_key: str,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        **provider_kwargs,
    ) -> AsyncIterable[bytes]:
        """
        Стримить файл чанками. Рекомендуется для видео/больших архивов.
        """

    @abstractmethod
    async def delete(
        self,
        file_key: str,
        **provider_kwargs,
    ):
        """
        Удалить файл. Возвращает True при успешном выполнении запроса.
        """

    @abstractmethod
    async def exists(
        self,
        file_key: str,
        **provider_kwargs,
    ) -> bool:
        """
        Проверить существование объекта без скачивания содержимого.
        """

    @abstractmethod
    async def get_presigned_url(
        self,
        file_key: str,
        expires_in: int = DEFAULT_EXPIRES_IN,
        http_method: str = "GET",
        **provider_kwargs,
    ) -> str:
        """
        Сгенерировать временную ссылку для прямого доступа.
        """
