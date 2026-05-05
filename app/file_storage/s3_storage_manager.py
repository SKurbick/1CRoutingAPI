import asyncio
from contextlib import AsyncExitStack
import hashlib
import json
from typing import Any, Self
import logging

from aiobotocore.session import AioSession, get_session
from aiobotocore.config import AioConfig
from types_aiobotocore_s3.client import S3Client

from .s3_file_storage import S3FileStorage


LOGGER = logging.getLogger(__name__)


class S3StorageManager:
    """
    Менеджер S3-хранилищ с гарантией одного экземпляра на уникальную конфигурацию.
    """

    __instances: dict[str, Self] = {}
    __creation_locks: dict[str, asyncio.Lock] = {}
    __global_lock: asyncio.Lock | None = None

    def __init__(
        self,
        region_name: str,
        bucket_name: str,
        aws_access_key_id: str,
        endpoint_url: str,
        aws_secret_access_key: str,
        url_gen_config: dict[str, Any] | None = None,
        dns_subdomain: str | None = None,
        **client_kwargs: Any,
    ):
        self._bucket_name = bucket_name
        self._endpoint_url = endpoint_url
        self._aws_access_key_id = aws_access_key_id
        self._aws_secret_access_key = aws_secret_access_key
        self._region_name = region_name
        self._url_gen_config = url_gen_config or {}
        self._dns_subdomain = dns_subdomain or None
        self._client_kwargs = client_kwargs

        self._client: S3Client | None = None
        self._url_gen_client: S3Client | None = None
        self._storage: S3FileStorage | None = None
        self._instance_lock = asyncio.Lock()
        self._key: str | None = None  # кэшированный ключ конфигурации
        self._async_exit_stack: AsyncExitStack | None = None

    async def __aenter__(self) -> Self:
        async with self._instance_lock:
            if self._storage is not None:
                return

            key = self._get_key()

            if key in self.__instances:
                existing = self.__instances[key]

                if existing._storage is not None:
                    self._storage = existing._storage
                    self._client = existing._client
                    self._url_gen_client = existing._url_gen_client
                    return

            await self._create_clients()
            self.__instances[key] = self

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        await self.close()

        if self._async_exit_stack is not None:
            try:
                await self._async_exit_stack.aclose()
            except Exception:
                pass

            self._async_exit_stack = None

    @classmethod
    def _get_global_lock(cls) -> asyncio.Lock:
        """
        Инициализация глобальной блокировки.
        """
        if cls.__global_lock is None:
            cls.__global_lock = asyncio.Lock()

        return cls.__global_lock

    @staticmethod
    def _make_config_key(
        bucket_name: str,
        endpoint_url: str,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        region_name: str,
        url_gen_config: dict[str, Any] | None = None,
        dns_subdomain: str | None = None,
        **client_kwargs: Any,
    ) -> str:
        """
        Создать детерминированный ключ для кэширования на основе конфигурации.
        """
        config = {
            "bucket": bucket_name,
            "endpoint": endpoint_url,
            "access_key": aws_access_key_id,
            "region": region_name,
            "url_gen": url_gen_config or {},
            "subdomain": dns_subdomain,
            **{k: v for k, v in client_kwargs.items() if k not in ("aws_secret_access_key",)},
        }

        config["secret_key_hash"] = hashlib.sha256(aws_secret_access_key.encode()).hexdigest()

        key_str = json.dumps(config, sort_keys=True, default=str)
        return hashlib.sha256(key_str.encode()).hexdigest()

    def _get_key(self) -> str:
        """
        Получить кэшированный ключ конфигурации экземпляра.
        """
        if self._key is None:
            self._key = self._make_config_key(
                bucket_name=self._bucket_name,
                endpoint_url=self._endpoint_url,
                aws_access_key_id=self._aws_access_key_id,
                aws_secret_access_key=self._aws_secret_access_key,
                region_name=self._region_name,
                url_gen_config=self._url_gen_config,
                dns_subdomain=self._dns_subdomain,
                **self._client_kwargs,
            )

        return self._key

    @classmethod
    async def get_instance(
        cls,
        bucket_name: str,
        endpoint_url: str,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        region_name: str,
        url_gen_config: dict[str, Any] | None = None,
        dns_subdomain: str | None = None,
        **client_kwargs: Any,
    ) -> Self:
        """
        Получить существующий экземпляр или создать новый.
        """
        key = cls._make_config_key(
            bucket_name=bucket_name,
            endpoint_url=endpoint_url,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
            url_gen_config=url_gen_config,
            dns_subdomain=dns_subdomain,
            **client_kwargs,
        )

        if key in cls.__instances:
            return cls.__instances[key]

        async with cls._get_global_lock():
            if key not in cls.__creation_locks:
                cls.__creation_locks[key] = asyncio.Lock()
        key_lock = cls.__creation_locks[key]

        async with key_lock:
            if key in cls.__instances:
                return cls.__instances[key]

            instance = cls(
                bucket_name=bucket_name,
                endpoint_url=endpoint_url,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=region_name,
                url_gen_config=url_gen_config,
                dns_subdomain=dns_subdomain,
                **client_kwargs,
            )
            try:
                await instance._create_clients()
            except Exception:
                raise

            cls.__instances[key] = instance
            return instance

    async def _create_clients(self) -> None:
        """
        Создать основной клиент и опционально отдельный для генерации URL.
        """
        if self._async_exit_stack is None:
            self._async_exit_stack = AsyncExitStack()

        session: AioSession = get_session()

        config = AioConfig(
            retries={"max_attempts": 3, "mode": "adaptive"},
            connect_timeout=5,
            read_timeout=15,
            request_checksum_calculation="when_required",
            response_checksum_validation="when_required",
            s3={"addressing_style": "path"},
        )

        client_params = {
            "service_name": "s3",
            "endpoint_url": self._endpoint_url,
            "aws_access_key_id": self._aws_access_key_id,
            "aws_secret_access_key": self._aws_secret_access_key,
            "region_name": self._region_name,
            "config": config,
            **self._client_kwargs,
        }

        client_params = {k: v for k, v in client_params.items() if v is not None}

        self._client = await self._async_exit_stack.enter_async_context(session.create_client(**client_params))

        if self._url_gen_config:
            url_gen_params = {**client_params, **self._url_gen_config}
            self._url_gen_client = await self._async_exit_stack.enter_async_context(
                session.create_client(**url_gen_params)
            )
        else:
            self._url_gen_client = None

        self._storage = S3FileStorage(
            client=self._client,
            bucket_name=self._bucket_name,
            url_gen_client=self._url_gen_client,
            subdomain_url=self._dns_subdomain,
        )

        LOGGER.info(f"Созданы клиенты файлового хранилища: {self._bucket_name}")

    @property
    def storage(self) -> S3FileStorage:
        """
        Готовый к работе экземпляр S3FileStorage.
        """
        if self._storage is None:
            raise RuntimeError(
                "Файловое хранилище не инициализировано. Используйте await S3StorageManager.get_instance()."
            )

        return self._storage

    @property
    def client(self) -> S3Client:
        """
        Прямой доступ к S3Client для низкоуровневых операций.
        """
        if self._client is None:
            raise RuntimeError("S3Client не инициализирован. Используйте await S3StorageManager.get_instance()")

        return self._client

    async def close(self) -> None:
        """
        Закрыть клиентов и удалить экземпляр из реестра.
        """
        if self._async_exit_stack is not None:
            await self._async_exit_stack.aclose()
            self._async_exit_stack = None

        self._storage = None

        key = self._get_key()
        self.__instances.pop(key, None)
        self.__creation_locks.pop(key, None)
        LOGGER.info(f"Cоединения с хранилищем закрыты: bucket_name={self._bucket_name}")
