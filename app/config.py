from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App settings, read from environment variables or a .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "agustinenriquez.dev API"
    app_version: str = "1.0.0"
    debug: bool = True
    database_url: str = "sqlite:///./blog.db"

    # Authentication
    secret_key: str = "your-secret-key-change-this-in-production"
    admin_password: str = "admin"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30


settings = Settings()
