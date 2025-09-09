import os
from functools import cache
from typing import Literal

from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)
from yarl import URL

ENV_FILE_PATH = (
    {
        "local": ".env",
        "ci": ".env.ci",
        "test": ".env.test",
    }
).get(os.getenv("ENV", "local"), ".env")


class BaseAppSettings(BaseSettings):
    """
    Base application settings.

    These parameters can be configured
    with environment variables.
    """

    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_file_encoding="utf-8",
        extra="allow",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return super().settings_customise_sources(
            settings_cls,
            init_settings,
            dotenv_settings,
            env_settings,
            file_secret_settings,
        )


class Settings(BaseAppSettings):
    """
    Application settings.

    These parameters can be configured
    with environment variables.
    """

    app_title: str = "Coffee Shop API"
    app_name: str = "coffee_shop"
    env: Literal["local", "test", "ci", "dev", "prod"] = "prod"
    root_path: str = ""
    domain: str = "example.com"

    debug: bool = True

    documentation_enabled: bool = True
    documentation_username: str = ""
    documentation_password: str = ""
    openapi_url: str = "/openapi.json"

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "postgres"
    postgres_password: str = ""
    postgres_db: str = ""
    postgres_echo: bool = False

    sentry_dsn: str | None = None

    prometheus_metrics_key: str = "secret"

    @property
    def postgres_url(self) -> str:
        return str(
            URL.build(
                scheme="postgresql+asyncpg",
                host=self.postgres_host,
                port=self.postgres_port,
                user=self.postgres_user,
                password=self.postgres_password,
                path=f"/{self.postgres_db}",
            )
        )


class RedisSettings(BaseAppSettings):
    class Config:
        env_prefix = "redis_"

    host: str = "redis"
    port: int = 6379
    database: int = 0

    @property
    def url(self) -> str:  # pragma: no cover
        return f"redis://{self.host}:{self.port}/{self.database}"


class JWTAuthSettings(BaseAppSettings):
    class Config:
        env_prefix = "jwt_"

    secret_key: str = ""
    algorithm: str = "HS256"
    access_token_expire: int = 1800
    ref_token_expire: int = 604800


class SMTPSettings(BaseAppSettings):
    class Config:
        env_prefix = "smtp_"

    host: str = "smtp.zoho.eu"
    port: int = 587
    user: str = ""
    password: str = ""
    use_tls: bool = True
    use_ssl: bool = False
    sender_email: str = ""


@cache
def get_settings() -> Settings:
    return Settings()


@cache
def get_redis_settings() -> RedisSettings:
    return RedisSettings()


@cache
def get_jwt_auth_settings() -> JWTAuthSettings:
    return JWTAuthSettings()


@cache
def get_smtp_settings() -> SMTPSettings:
    return SMTPSettings()


settings = get_settings()
redis_settings = get_redis_settings()
jwt_settings = get_jwt_auth_settings()
smtp_settings = get_smtp_settings()
