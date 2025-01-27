from dotenv import load_dotenv, find_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv(find_dotenv())


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    db_engine: str
    db_name: str
    postgres_user: str
    postgres_password: str
    db_host: str
    db_port: int
    database_url: str = None

    line_provider_token: str = (
        "f3fb8928bad49887d2089f5ad04c2cb634bb1980db77fc8c3b111edad34f4eb7"
    )

    meter_coefficient: int = 1000
    wsg_standard: int = 4326

    es_address: str

    log_level: str = "INFO"


settings = Settings()
