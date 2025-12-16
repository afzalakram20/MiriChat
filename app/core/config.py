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

    DO_MODEL_ACCESS_KEY: str = ""
    DO_MODEL_ID: str = ""
    DO_INFERENCE_BASE_URL: str = ""
    DO_TEMPERATURE: float 
    DO_MAX_TOKENS: int  
    DO_TIMEOUT: float  
    

    # DB
    MYSQL_DSN: str = ""

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
    HUGGINGFACE_HUB_TOKEN: str = ""

    MONGODB_URI: str = "mongodb+srv://ishratali574_db_user:<db_password>@cluster0.sbkqu41.mongodb.net/?appName=Cluster0"
    MONGODB_DB: str = "ew_ai_chat_db"
    MONGODB_COLLECTION: str = "ai_chat_history"

    REDIS_URL: str = "redis://localhost:6379/0"
    TOOL_NAME: str = "EW"



    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def models_list(self) -> List[dict[str, str]]:
        return [
            {"id": self.OPENAI_MODEL, "name": "OpenAI (default)", "key": "openai"},
            {"id": "deepseek-r1-distill-llama-70b", "name": "DeepSeek R1 Distill Llama 70B", "key": "do_serverless"},
            {"id": "llama3.3-70b-instruct", "name": "Llama 3.3 70B Instruct", "key": "do_serverless"},
            {"id": "llama3-8b-instruct", "name": "Llama 3 8B Instruct", "key": "do_serverless"},
        ]


settings = Settings()
