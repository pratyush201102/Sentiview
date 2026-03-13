from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Sentiview API"
    app_env: str = "development"
    api_port: int = 8000

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5433/sentiview"

    reddit_user_agent: str = "sentiview/0.1"
    reddit_base_url: str = "https://www.reddit.com"
    default_fetch_limit: int = 25


settings = Settings()
