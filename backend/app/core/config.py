import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Financas Pessoais"
    app_host: str = "0.0.0.0"
    app_port: int = 8080
    log_level: str = "INFO"

    database_url: str = "sqlite:///./data/financas.db"

    # CORS - URLs que podem chamar o backend
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Autenticacao
    secret_key: str = "change-me-in-production"
    codigo_cadastro: str = ""
    jwt_expire_days: int = 7
    jwt_algorithm: str = "HS256"

    # Integracoes
    brapi_token: str = ""

    @property
    def cors_list(self) -> list:
        """Retorna lista de URLs de CORS."""
        # Aceita tambem variavel PORT do Railway (usa mesma logica)
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def db_path(self) -> Path:
        """So funciona para SQLite. Retorna Path do arquivo."""
        if self.database_url.startswith("sqlite"):
            path = Path(self.database_url.replace("sqlite:///", ""))
            path.parent.mkdir(parents=True, exist_ok=True)
            return path
        return Path("./data/financas.db")

    @property
    def porta_efetiva(self) -> int:
        """
        Retorna a porta a usar. Railway/Heroku setam a variavel PORT
        dinamicamente. Se existir, ela tem prioridade sobre APP_PORT.
        """
        return int(os.environ.get("PORT", self.app_port))


settings = Settings()