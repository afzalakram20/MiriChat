from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    project_name: str = "Sports"
    APP_ENV: str = "dev"
    PORT: int = 8081
    CORS_ORIGINS: str = "http://localhost:4200"

    # LLM

    PROJECT_OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_API_KEY: str = ""
    LLM_PROVIDER: str = ""
    PINECONE_API_KEY: str = ""
    HG_EMBEDDING_MODEL: str = ""

    BEDROCK_REGION: str = "us-east-1"
    BEDROCK_ACCESS_KEY: str | None = None
    BEDROCK_SECRET_KEY: str | None = None
    BEDROCK_MODEL_ID: str = ""
    BEDROCK_TEMPERATURE: float = 0.1
    BEDROCK_MAX_TOKENS: int = 1024

    # DB
    MYSQL_DSN: str = "mysql+pymysql://root@127.0.0.1:3306/horizon_extra_work_tool"

    # Limits & logging
    MAX_LIMIT: int = 100
    SQL_TIMEOUT_SECONDS: int = 15
    LOG_LEVEL: str = "INFO"
    LOG_FILE_PATH: str = "./logs/app.log"
    EMAIL_PROVIDER: str = "smtp"
    SMTP_HOST: str = "smtp.ethereal.email"
    EMAIL_FROM: str = "alexis44@ethereal.email"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = "alexis44@ethereal.email"
    SMTP_PASSWORD: str = "UC1wAFHdxmmzBqQUJ2"
    SMTP_USE_TLS: bool = True


@property
def cors_origins_list(self) -> List[str]:
    return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
