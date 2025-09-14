from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    database_url: str
    redis_url: str 
    secret_key: str 
    algorithm: str 
    access_token_expire_minutes: int = 30

    class Config:
        env_file = ".env"


settings = Settings()