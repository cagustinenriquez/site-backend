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
    # Used only while data/users.json has no users (see app/users.py)
    admin_password: str = "admin"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Rate limiting (per client IP)
    rate_limit_enabled: bool = True
    rate_limit_default: str = "100/minute"
    rate_limit_login: str = "5/minute"


settings = Settings()
