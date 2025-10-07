from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
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


