from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # 环境
    ENV: str = "dev"

    # 安全
    SECRET_KEY: str = "CHANGE_ME_TO_A_RANDOM_LONG_STRING"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # 数据库
    DATABASE_URL: str = "sqlite:///./data.db"

    # 跨域（开发时前端 Vite 默认 5173）
    CORS_ORIGINS: str = "http://localhost:5173"

    # 模型数据目录（默认读取本仓库的前端 public/model_cache）
    # 你可以改成绝对路径，或在部署时挂载外部存储。
    MODEL_CACHE_DIR: str = str(
        (Path(__file__).resolve().parents[3] / "frontend" / "public" / "model_cache").resolve()
    )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

