# config.py
# application configuration settings using pydantic-settings

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
    )

    def get_s3_base_url(self) -> str:
        if self.s3_endpoint_url: # for MinIO or custom S3-compatible services, we use the endpoint URL as the base
            return f"{self.s3_endpoint_url}/{self.s3_bucket_name}"
        return f"https://{self.s3_bucket_name}.s3.{self.s3_region}.amazonaws.com"
    
    debug: bool = True # fields in .env will override these defaults
    # database_url: str = "sqlite+aiosqlite:///./blog.db" # older sqlite url, replaced with postgres below
    database_url: str = "postgresql+asyncpg://user:password@localhost/blogpost1.3"  # example for PostgreSQL, set in .env file

    secret_key: SecretStr = "my-secret-key-2026"  # loaded from .env file,
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # S3 Configuration
    s3_bucket_name: str
    s3_region: str = "us-east-1"
    s3_access_key_id: SecretStr | None = None
    s3_secret_access_key: SecretStr | None = None
    s3_endpoint_url: str | None = None

    max_upload_size_bytes: int = 2 * 1024 * 1024  # 2 MB
    
    posts_per_page: int = 10

    reset_token_expire_minutes: int = 60
    
    # email configuration for password reset emails
    mail_server: str = "localhost"  # your email provider's SMTP server (e.g., "smtp.gmail.com").
    mail_port: int = 587  #  587 is standard for TLS-encrypted email, alternative: 465 (SSL)
    mail_username: str = ""  # often your email address
    mail_password: SecretStr = SecretStr("")  # set in .env 
    mail_from: str = "noreply@example.com"
    mail_use_tls: bool = True

    frontend_url: str = "http://localhost:8000"


settings = Settings()  # type: ignore[call-arg] # Loaded from .env file