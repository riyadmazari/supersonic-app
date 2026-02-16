from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://supersonic_user:supersonic_pass@db:5432/supersonic_db"
    SECRET_KEY: str = "change-me-to-a-random-secret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    GEMINI_API_KEY: str | None = None

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
