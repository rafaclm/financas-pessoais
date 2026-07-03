"""
Configuracao do banco de dados.
Suporta SQLite e PostgreSQL alternando via DATABASE_URL no .env.

Exemplos:
- SQLite:     sqlite:///./data/financas.db
- PostgreSQL: postgresql+psycopg2://usuario:senha@host:5432/nomedobanco
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from loguru import logger
from app.core.config import settings


def _detectar_tipo_banco(url: str) -> str:
    """Retorna 'sqlite' ou 'postgresql'."""
    if url.startswith("sqlite"):
        return "sqlite"
    if url.startswith(("postgresql", "postgres")):
        return "postgresql"
    return "desconhecido"


tipo_banco = _detectar_tipo_banco(settings.database_url)

# Ajustes especificos por tipo de banco
if tipo_banco == "sqlite":
    # SQLite precisa desse parametro para funcionar bem com FastAPI
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        echo=False,
    )
    logger.info(f"🗄️ Banco SQLite: {settings.database_url}")
elif tipo_banco == "postgresql":
    # PostgreSQL - configuracoes de pool
    engine = create_engine(
        settings.database_url,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,   # Testa conexao antes de usar
        pool_recycle=3600,    # Recicla conexoes antigas (1 hora)
        echo=False,
    )
    # Extrai só nome do host/db para nao expor senha nos logs
    partes = settings.database_url.split("@")
    if len(partes) > 1:
        info = partes[1]
    else:
        info = "url_sem_senha"
    logger.info(f"🐘 Banco PostgreSQL: {info}")
else:
    logger.warning(f"⚠️ Tipo de banco desconhecido: {settings.database_url}")
    engine = create_engine(settings.database_url, echo=False)


SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)