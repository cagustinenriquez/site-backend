from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from pathlib import Path


class Settings(BaseSettings):
    app_name: str = "agustinenriquez.dev API"
    app_version: str = "1.0.0"
    debug: bool = True
    database_url: str = "sqlite:///./blog.db"
    data_dir: str = "data"  # Directory for storing JSON data files

    model_config = ConfigDict(env_file=".env", extra="ignore")


settings = Settings()

# Ensure data directory path is absolute
DATA_DIR = Path(settings.data_dir).resolve()
DATA_DIR.mkdir(parents=True, exist_ok=True)
