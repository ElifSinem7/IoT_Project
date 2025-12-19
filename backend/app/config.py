from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "Know The Air Backend"
    API_KEY: str = "change-me-please"
    DB_PATH: str = "./data/air_quality.db"
    CORS_ORIGINS: str = "http://localhost:5173"
    BASELINE_SECONDS: int = 60
    WARN_INCREASE_PCT: float = 35.0
    HIGH_INCREASE_PCT: float = 80.0


    def cors_list(self) -> List[str]:
        return [x.strip() for x in self.CORS_ORIGINS.split(",") if x.strip()]

settings = Settings()
