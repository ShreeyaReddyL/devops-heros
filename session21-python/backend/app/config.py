"""Application settings loaded from the environment."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "CampusFix API"
    version: str = "1.0.0"
    database_url: str = "postgresql+psycopg://campusfix:campusfix@localhost:5432/campusfix"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()