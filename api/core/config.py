from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 应用
    app_name: str = "Facebook Video Script Extractor API"
    debug: bool = False

    # API Key（简单认证，适合小团队）
    api_key: str = "dev-api-key-change-me"

    # Redis / Celery
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    # 模型默认参数
    default_model_size: str = "small"
    default_device: str = "cpu"
    default_language: str = "auto"

    # 路径
    temp_dir: str = "./temp"
    output_dir: str = "./output"

    # OpenAI（可选）
    openai_api_key: str | None = None

    # 结果保留天数
    result_retention_days: int = 7

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
