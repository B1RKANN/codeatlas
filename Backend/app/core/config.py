from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "CodeAtlas Auth API"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/codeatlas"
    secret_key: str = "change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
