import os
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Monolithic Banking Management System"
    API_V1_STR: str = "/api"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretjwtkeyforbankingapplication123456!")
    REFRESH_SECRET_KEY: str = os.getenv("REFRESH_SECRET_KEY", "supersecretrefreshjwtkeyforbankingapplication123456!")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:postgres@localhost:5432/banking_db"
    )

    # File Storage (Azure Blob Storage)
    AZURE_STORAGE_CONNECTION_STRING: str = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
    AZURE_STORAGE_ACCOUNT_NAME: str = os.getenv("AZURE_STORAGE_ACCOUNT_NAME", "")
    AZURE_STORAGE_BLOB_ENDPOINT: str = os.getenv("AZURE_STORAGE_BLOB_ENDPOINT", "")
    AZURE_STORAGE_ACCOUNT_URL: str = os.getenv(
        "AZURE_STORAGE_ACCOUNT_URL",
        AZURE_STORAGE_BLOB_ENDPOINT
    )
    AZURE_STORAGE_CONTAINER_NAME: str = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "documents")
    AZURE_CONTAINER_NAME: str = os.getenv(
        "AZURE_CONTAINER_NAME",
        AZURE_STORAGE_CONTAINER_NAME
    )
    REQUIRE_AZURE_STORAGE: bool = os.getenv("REQUIRE_AZURE_STORAGE", "false").lower() == "true"

    # Service Bus
    SERVICE_BUS_NAMESPACE: str = os.getenv("SERVICE_BUS_NAMESPACE", "")
    SERVICE_BUS_QUEUE: str = os.getenv("SERVICE_BUS_QUEUE", "")

    model_config = ConfigDict(case_sensitive=True)

settings = Settings()
