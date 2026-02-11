from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://supersonic_user:supersonic_pass@db:5432/supersonic_db"
    SECRET_KEY: str = "change-me-to-a-random-secret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    AI_API_BASE_URL: str = "http://localhost:8000/ai"
    AI_API_KEY: str = "not-needed-for-stub"

    class Config:
        env_file = ".env"


settings = Settings()
