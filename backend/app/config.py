from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ================== GENERAL ==================
    APP_NAME: str = "Know The Air Backend"
    API_KEY: str = "know-the-air-you-breaathe-in"
    DB_PATH: str = "./data/air_quality.db"
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5500,http://127.0.0.1:5500"

    # ================== MQTT SETTINGS ==================
    MQTT_BROKER: str = "broker.emqx.io"
    MQTT_PORT: int = 1883
    MQTT_TOPIC_PREFIX: str = "kayseri/air_quality/"

    # ================== BASELINE / TREND ==================
    BASELINE_SECONDS: int = 60
    WARN_INCREASE_PCT: float = 35.0
    HIGH_INCREASE_PCT: float = 80.0

    # ================== TEST MODE LIMITS ==================
    ECO2_TEST_MIN: int = 350
    ECO2_TEST_MAX: int = 600

    TVOC_TEST_MIN: int = 0
    TVOC_TEST_MAX: int = 120

    # ================== HYSTERESIS ==================
    ECO2_HYST: int = 20
    TVOC_HYST: int = 10

    # ================== DELTA DETECTION ==================
    ECO2_DELTA_PPM: int = 30
    TVOC_DELTA_PPB: int = 15
    TEMP_DELTA_C: float = 0.5
    HUM_DELTA_RH: float = 2.0
    PRESS_DELTA_HPA: float = 1.0

    # ================== HELPERS ==================
    def cors_list(self) -> List[str]:
        return [x.strip() for x in self.CORS_ORIGINS.split(",") if x.strip()]


settings = Settings()