# 配置管理
from pydantic import BaseSettings


class Settings(BaseSettings):
    service_name: str = "default"
    port: int = 8080
    log_level: str = "INFO"
    database_url: str = "postgresql://localhost/db"

    class Config:
        env_file = ".env"

settings = Settings()
