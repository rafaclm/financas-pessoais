"""
Configuracao do banco de dados.
Suporta SQLite e PostgreSQL alternando via DATABASE_URL no .env.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from loguru import logger
from app.core.config import settings


def _ajustar_url_railway(url: str) -> str:
    """
    Railway usa 'postgresql://' mas SQLAlchemy prefere 'postgresql+psycopg2://'.
    Faz o ajuste automatico se necessario.
    """
    if url.startswith("postgres://"):
        # Alguns provedores usam 'postgres://' - ajusta
        url = "postgresql+psycopg2://" + url[len("postgres://"):]
    elif url.startswith("postgresql://") and "psycopg2" not in url:
        # Railway padrao - adiciona +psycopg2
        url = "postgresql+psycopg2://" + url[len("postgresql://"):]
    return url


def _detectar_tipo_banco(url: str) -> str:
    """Retorna 'sqlite' ou 'postgresql'."""
    if url.startswith("sqlite"):
        return "sqlite"
    if url.startswith(("postgresql", "postgres")):
        return "postgresql"
    return "desconhecido"


# Ajusta URL se necessario
database_url = _ajustar_url_railway(settings.database_url)
tipo_banco = _detectar_tipo_banco(database_url)


if tipo_banco == "sqlite":
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
        echo=False,
    )
    logger.info(f"🗄️ Banco SQLite: {database_url}")
elif tipo_banco == "postgresql":
    engine = create_engine(
        database_url,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=False,
    )
    partes = database_url.split("@")
    info = partes[1] if len(partes) > 1 else "url_sem_senha"
    logger.info(f"🐘 Banco PostgreSQL: {info}")
else:
    logger.warning(f"⚠️ Tipo de banco desconhecido: {database_url}")
    engine = create_engine(database_url, echo=False)


SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)