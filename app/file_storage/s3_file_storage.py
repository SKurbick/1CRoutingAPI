import logging

from botocore.exceptions import ClientError
from types_aiobotocore_s3.client import S3Client

from .base import (
    IFileStorage,
    FileStorageError,
    StorageFileNotFoundError,
)
from .base.constants import DEFAULT_CHUNK_SIZE, DEFAULT_EXPIRES_IN


logger = logging.getLogger(__name__)


class S3FileStorage(IFileStorage):
    """
    S3-совместимое файловое хранилище.
    """

    def __init__(
        self,
        client: S3Client,
        bucket_name: str,
        url_gen_client: S3Client | None = None,
        subdomain_url: str | None = None,
    ):
        logger.info("Инициализируем s3 storage...")
        self._bucket_name = bucket_name
        self._client = client
        self._url_gen_client = url_gen_client
        self._subdomain_url = subdomain_url

    async def upload(
        self,
        file_key,
        data,
        content_type=None,
        metadata=None,
        **provider_kwargs,
    ):
        put_kwargs: dict = {
            "Bucket": self._bucket_name,
            "Key": file_key,
            "Body": data,
        }

        if content_type:
            put_kwargs["ContentType"] = content_type

        if metadata:
            put_kwargs["Metadata"] = {k: str(v) for k, v in metadata.items()}

        put_kwargs.update(provider_kwargs)

        await self._client.put_object(**put_kwargs)
        logger.debug(f"Файл {file_key} успешно загружен в бакет {self._bucket_name}")
        return file_key

    async def download(
        self,
        file_key,
        **provider_kwargs,
    ):
        try:
            response = await self._client.get_object(
                Bucket=self._bucket_name,
                Key=file_key,
                **provider_kwargs,
            )

            async with response["Body"] as stream:
                return await stream.read()
        except ClientError as e:
            message = f"Ошибка при скачивании файла {file_key}: {e}"

            if message.find("NoSuchKey") != -1:
                message = f"Объект {self._bucket_name}:{file_key} не найден."
                raise StorageFileNotFoundError(message)

            raise FileStorageError(message)

    async def download_stream(
        self,
        file_key,
        chunk_size=DEFAULT_CHUNK_SIZE,
        **provider_kwargs,
    ):
        try:
            response = await self._client.get_object(
                Bucket=self._bucket_name,
                Key=file_key,
                **provider_kwargs,
            )

            async with response["Body"] as stream:
                while chunk := await stream.content.read(chunk_size):
                    yield chunk
        except ClientError as e:
            message = f"Ошибка при стриминге файла {file_key}: {e}"

            if message.find("NoSuchKey") != -1:
                message = f"Объект {self._bucket_name}:{file_key} не найден."
                raise StorageFileNotFoundError(message)

            raise FileStorageError(message)

    async def delete(
        self,
        file_key,
        **provider_kwargs,
    ):
        try:
            await self._client.delete_object(
                Bucket=self._bucket_name,
                Key=file_key,
                **provider_kwargs,
            )
            logger.debug(f"Файл {file_key} успешно удалён из бакета {self._bucket_name}")
        except ClientError as e:
            message = f"Ошибка при удалении файла {file_key}: {e}"
            raise FileStorageError(message)

    async def exists(
        self,
        file_key,
        **provider_kwargs,
    ):
        try:
            await self._client.head_object(
                Bucket=self._bucket_name,
                Key=file_key,
                **provider_kwargs,
            )
            return True
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")

            if error_code in ("404", "NoSuchKey", "NotFound"):
                return False

            message = f"Ошибка при проверке существования файла {file_key}: {e}"
            raise FileStorageError(message)

    async def get_presigned_url(
        self,
        file_key,
        expires_in=DEFAULT_EXPIRES_IN,
        http_method="GET",
        **provider_kwargs,
    ):
        if not await self.exists(file_key):
            message = f"Объект {self._bucket_name}:{file_key} не найден."
            raise StorageFileNotFoundError(message)

        normilized_method = http_method.upper()

        if normilized_method == "GET":
            client_method = "get_object"
        elif normilized_method == "PUT":
            client_method = "put_object"
        elif normilized_method == "DELETE":
            client_method = "delete_object"
        else:
            client_method = "get_object"

        client_for_generate = self._url_gen_client or self._client

        url = await client_for_generate.generate_presigned_url(
            ClientMethod=client_method,
            Params={
                "Bucket": self._bucket_name,
                "Key": file_key,
                **{k: v for k, v in provider_kwargs.items() if k not in ("Bucket", "Key")},
            },
            ExpiresIn=expires_in,
            HttpMethod=normilized_method,
        )

        if self._subdomain_url is not None:
            url = self._change_dns_url_to_subdomain(url=url, file_key=file_key)
        logger.debug(f"Сгенерирована presigned URL для {file_key} на {expires_in} сек")

        return url

    def _change_dns_url_to_subdomain(self, url: str, file_key: str) -> str:
        if self._subdomain_url is not None:
            return f"{self._subdomain_url}/{file_key}{url.split(file_key)[1]}"

        return url
