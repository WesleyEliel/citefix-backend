import secrets
import warnings
from typing import Annotated, Any, Literal, Optional

from dotenv import load_dotenv
from pydantic import (
    AnyUrl,
    BeforeValidator,
    HttpUrl,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self

load_dotenv()


def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )
    # PROJECT INFOS
    PROJECT_NAME: str
    ADMIN_EMAIL: str
    DOMAIN: str = "localhost"

    # ENVIRONMENT
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    ENVIRONMENT: Literal["local", "development", "staging", "production"] = "local"
    FRONTEND_URL: str = "localhost:3000/"

    # SECURITY
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ENCRYPTION_ALGORITHM: str = "HS256"
    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyUrl] | str, BeforeValidator(parse_cors)
    ] = []
    ACCESS_TOKEN_EXPIRE_HOURS: int = 1
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 1
    EMAIL_VERIFY_TOKEN_EXPIRE_HOURS: int = 24

    # DATABASE
    MONGO_DATABASE_NAME: str
    ## In local env
    MONGO_DATABASE_URI: str = "mongodb://localhost:27017"
    ## Else
    MONGO_USERNAME: str = ""
    MONGO_PASSWORD: str = ""
    MONGO_HOST: str = ""
    MONGO_PORT: str = ""

    # JWT CONFIG
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 1

    # AWS CONFIGS
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str = "us-east-1"
    AWS_STORAGE_BUCKET_NAME: str
    AWS_STORAGE_ENDPOINT_URL: str

    # File upload settings

    # FILE UPLOAD
    MAX_UPLOAD_SIZE: int = 10  # in MB
    MAX_AVATAR_SIZE: int = 5  # 5MB

    # SENTRY
    SENTRY_DSN: HttpUrl | None = None

    # Email settings
    EMAIL_USERNAME: Optional[str] = ""
    EMAIL_PASSWORD: Optional[str] = ""
    EMAIL_FROM: str
    EMAIL_FROM_NAME: str = "Your App Name"
    EMAIL_PORT: int = 587
    EMAIL_SERVER: str

    @model_validator(mode="after")
    def _enforce_non_default_secrets(self) -> Self:
        self._check_default_secret("SECRET_KEY", self.SECRET_KEY)
        return self

    @field_validator('DEBUG', mode="before")
    def parse_debug(cls, v: Any) -> bool:
        if isinstance(v, str):
            return v.lower() in ["true", "1", "t", "y", "yes"]
        elif isinstance(v, int):
            return bool(int)
        raise ValueError(v)

    @field_validator('ENVIRONMENT')
    def validate_environment(cls, v: str) -> str:
        """Ensure environment is valid"""
        v = v.lower()
        if v not in {"local", "development", "staging", "production"}:
            return "development"
        return v

    @field_validator('LOG_LEVEL')
    def validate_log_level(cls, v: str) -> str:
        """Ensure log level is valid"""
        v = v.upper()
        if v not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            return "INFO"
        return v

    @field_validator('MAX_UPLOAD_SIZE')
    def convert_to_bytes(cls, v: int) -> int:
        """Convert MB to bytes"""
        return v * 1024 * 1024

    def _check_default_secret(self, var_name: str, value: str | None) -> None:
        if value == "changethis":
            message = (
                f'The value of {var_name} is "changethis", '
                "for security, please change it, at least for deployments."
            )
            if self.ENVIRONMENT == "local":
                warnings.warn(message, stacklevel=1)
            else:
                raise ValueError(message)


settings = Settings()  # type: ignore

