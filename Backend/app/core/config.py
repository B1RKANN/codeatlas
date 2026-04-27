from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "CodeAtlas API"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/codeatlas"
    secret_key: str = "change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.0-flash"
    gemini_timeout_seconds: int = 60
    gemini_max_retries: int = 2
    gemini_retry_backoff_seconds: float = 1.0
    analysis_max_zip_bytes: int = 100 * 1024 * 1024
    analysis_max_uncompressed_bytes: int = 300 * 1024 * 1024
    analysis_max_source_file_bytes: int = 512 * 1024
    analysis_max_files: int = 5000
    run_migrations_on_startup: bool = False

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
