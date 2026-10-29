from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# The project folder. .env and the default SQLite file are found relative to
# it, not to the current directory: on PythonAnywhere the WSGI process runs from
# your home folder, so a plain ".env" would never be found.
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """App settings, read from environment variables or the project's .env file."""

    model_config = SettingsConfigDict(env_file=PROJECT_ROOT / ".env", extra="ignore")

    app_name: str = "agustinenriquez.dev API"
    app_version: str = "1.0.0"
    debug: bool = True
    # Supabase/Postgres URL in production; local SQLite file by default
    database_url: str = f"sqlite:///{PROJECT_ROOT / 'data' / 'app.db'}"

    # Supabase REST API. When both are set, data goes through Supabase's HTTPS
    # API instead of DATABASE_URL: for hosts that block database connections
    # (PythonAnywhere free). The key must be the secret/service_role key; keep
    # it server-side only.
    supabase_url: str = ""
    supabase_key: str = ""

    @property
    def use_supabase_rest(self) -> bool:
        return bool(self.supabase_url and self.supabase_key)

    # Authentication
    secret_key: str = "your-secret-key-change-this-in-production"
    # Used only while the users table is empty (see app/users.py)
    admin_password: str = "admin"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Rate limiting (per client IP)
    rate_limit_enabled: bool = True
    rate_limit_default: str = "100/minute"
    rate_limit_login: str = "5/minute"


settings = Settings()
