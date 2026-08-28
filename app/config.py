from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "agustinenriquez.dev API"
    app_version: str = "1.0.0"
    debug: bool = True
    database_url: str = "sqlite:///./blog.db"

    class Config:
        env_file = ".env"


settings = Settings()
