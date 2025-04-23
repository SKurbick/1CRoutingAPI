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
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings: Settings = Settings()

