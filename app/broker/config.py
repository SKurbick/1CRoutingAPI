from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


# class _Settings(BaseSettings):
#     # App
#     DEBUG: bool = False

#     # RabbitMQ
#     RABBIT_PORT: int = 5672
#     RABBIT_HOST: str = "localhost"
#     RABBIT_USER: str
#     RABBIT_PASS: SecretStr

#     # rabbit exchanges
#     RABBIT_EXC_DOCGEN_REQUEST: str = "docgen.request.exchange"
#     RABBIT_EXC_DOCGEN_EVENT: str = "docgen.event.exchange"

#     # rabbit queues
#     RABBIT_Q_DOCGEN_BOX_LABEL: str = "docgen.box_label.queue"
#     RABBIT_Q_DOCGEN_UNIT_LABEL: str = "docgen.unit_label.queue"

#     # rabbit routing keys
#     RABBIT_RK_DOC_BOX_LABEL: str = "doc.box_label"
#     RABBIT_RK_DOC_UNIT_LABEL: str = "doc.unit_label"
#     RABBIT_RK_DOC_GENERATED_BOX_LABEL: str = "doc.generated.box_label"
#     RABBIT_RK_DOC_GENERATED_UNIT_LABEL: str = "doc.generated.unit_label"

#     # # minio
#     # AWS_SECRET_ACCESS_KEY: SecretStr
#     # AWS_ACCESS_KEY_ID: str
#     # AWS_REGION_NAME: str = "ru-central-1"
#     # FILE_STORAGE_HOST: str = "localhost"
#     # FILE_STORAGE_PORT: int = 9000
#     # FILE_STORAGE_DNS_HOST: str = "localhost"
#     # DOCGEN_BUCKET_NAME: str = "document-generator-bucket"

#     # @property
#     # def file_storage_url(self) -> str:
#     #     return f"http://{self.FILE_STORAGE_HOST}:{self.FILE_STORAGE_PORT}"

#     # @property
#     # def file_storage_dns_url(self) -> str:
#     #     return f"http://{self.FILE_STORAGE_DNS_HOST}:{self.FILE_STORAGE_PORT}"

#     model_config = SettingsConfigDict(
#         env_file=".env",
#         env_file_encoding="utf-8",
#         extra="ignore",
#     )


# @lru_cache(maxsize=1)
# def get_settings() -> _Settings:
#     return _Settings()

# SETTINGS = get_settings()
