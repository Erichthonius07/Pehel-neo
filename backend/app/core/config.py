from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str = "postgresql+psycopg://pehel:pehel@localhost:5432/pehel_neo"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "pehel-neo-dev-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    GROQ_API_KEY: str = ""
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "pehelminio"
    S3_SECRET_KEY: str = "pehelminio123"
    S3_BUCKET: str = "pehel-media"
    S3_REGION: str = "us-east-1"

    # MinIO aliases (storage_service.py uses these names)
    @property
    def MINIO_ENDPOINT(self) -> str:
        return self.S3_ENDPOINT

    @property
    def MINIO_ACCESS_KEY(self) -> str:
        return self.S3_ACCESS_KEY

    @property
    def MINIO_SECRET_KEY(self) -> str:
        return self.S3_SECRET_KEY

    @property
    def MINIO_BUCKET(self) -> str:
        return self.S3_BUCKET
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: str = "http://localhost:3000"
    PILOT_CITY: str = "Kanpur"
    PILOT_STATE: str = "Uttar Pradesh"
    MOCK_OTP: bool = True
    DEFAULT_MOCK_OTP: str = "123456"
    PRESENCE_CHECK_BUFFER_METERS: int = 200
    DUPLICATE_RADIUS_METERS: int = 150
    REPEAT_FAILURE_RADIUS_METERS: int = 80

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


@lru_cache()
def get_settings() -> Settings:
    return Settings()
