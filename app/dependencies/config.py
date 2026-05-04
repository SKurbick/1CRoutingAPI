from functools import lru_cache
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    # RabbitMQ
    RABBIT_PORT: int = 5672
    RABBIT_HOST: str = "localhost"
    RABBIT_USER: str
    RABBIT_PASS: SecretStr
    RABBIT_VHOST: str = '/'
    
    # rabbit exchanges
    RABBIT_EXC_DOCGEN_REQUEST: str = "docgen.request.exchange"
    RABBIT_EXC_DOCGEN_EVENT: str = "docgen.event.exchange"

    # rabbit queues
    RABBIT_Q_DOCGEN_BOX_LABEL: str = "docgen.box_label.queue"
    RABBIT_Q_DOCGEN_BOX_LABEL_RESPONSE: str = "docgen.box_label.event.queue"
    RABBIT_Q_DOCGEN_UNIT_LABEL: str = "docgen.unit_label.queue"

    # rabbit routing keys
    RABBIT_RK_DOC_BOX_LABEL: str = "doc.box_label"
    RABBIT_RK_DOC_UNIT_LABEL: str = "doc.unit_label"
    RABBIT_RK_DOC_GENERATED_BOX_LABEL: str = "doc.generated.box_label"
    RABBIT_RK_DOC_GENERATED_UNIT_LABEL: str = "doc.generated.unit_label"
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: str
    APP_IP_ADDRESS: str
    APP_PORT: int
    INITIAL_SERVICE_TOKEN: str
    TOKEN_HEADER: str = "X-Service-Token"
    ONE_C_LOGIN: str
    ONE_C_PASSWORD: str
    ONE_C_BASE_URL: str
    WMS_API_URL_MOVEMENTS: str
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

account_inn_map = data = {
            "Вектор": "9715401127",
            "Тоноян": "503822685772",
            "Даниелян": "615490441596",
            "Лопатина": "771575954343",
            "Оганесян": "774308962107",
            "Хачатрян": "771675966776",
            "Пилосян": "753619553871",
            "Старт": "5029275624",
            "Старт2": "5029275624",
            "Вектор2": "9715401127"

        }
settings: Settings = Settings()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()



SETTINGS = get_settings()



