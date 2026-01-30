from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Server
    port: int = 3002
    node_env: str = "development"

    # Database
    mongodb_uri: str = "mongodb://127.0.0.1:27017/tools-sync-py"

    # JWT
    jwt_secret: str = "dev-secret-change-in-production-abc123"
    jwt_refresh_secret: str = "dev-refresh-secret-change-in-production-xyz789"
    jwt_expires_minutes: int = 15
    jwt_refresh_expires_days: int = 7

    # CORS
    cors_origin: str = "http://localhost:5173"
    cookie_domain: str = ""

    # Payload
    max_payload_size: int = 50 * 1024 * 1024  # 50MB

    # SMTP
    smtp_host: str = ""
    smtp_port: int = 465
    smtp_secure: bool = True
    smtp_user: str = ""
    smtp_pass: str = ""
    smtp_from: str = ""

    # Frontend
    frontend_url: str = "http://localhost:5173"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def is_production(self) -> bool:
        return self.node_env == "production"


settings = Settings()
