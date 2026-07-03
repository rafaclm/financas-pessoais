import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, func
from loguru import logger
from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.core.middleware_auth import middleware_auth
from app.infrastructure.db.base import Base
from app.infrastructure.db import models  # noqa: F401
from app.api.router import api_router
from app.seeds import run_seeds


def _bootstrap_posicao_atual():
    """Recalcula posicao atual dos ativos na inicializacao."""
    from app.infrastructure.db.models import PosicaoAtualAtivo, AporteBolsa
    from app.services.posicao_atual import recalcular_todas_posicoes

    with SessionLocal() as db:
        ja_tem = db.scalar(select(func.count(PosicaoAtualAtivo.id)))
        if ja_tem and ja_tem > 0:
            logger.info(f"Posição atual já existe ({ja_tem} ativos). Bootstrap pulado.")
            return

        qtd_aportes = db.scalar(select(func.count(AporteBolsa.id))) or 0
        if qtd_aportes == 0:
            logger.info("Nenhum aporte cadastrado. Bootstrap pulado.")
            return

        logger.info(f"Calculando posição atual com base em {qtd_aportes} aportes...")
        r = recalcular_todas_posicoes(db)
        logger.info(f"Bootstrap concluído: {r['mensagem']}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Iniciando aplicação...")
    logger.info(f"🌍 CORS permitidos: {settings.cors_list}")
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        run_seeds(db)
    _bootstrap_posicao_atual()
    logger.info("✅ Banco pronto.")
    logger.info("🛡️ Autenticação global ATIVADA")
    yield
    logger.info("👋 Encerrando aplicação.")


app = FastAPI(
    title=settings.app_name,
    version="0.8.0",
    lifespan=lifespan,
)

# CORS - precisa vir antes do middleware de auth
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware de autenticacao global
app.middleware("http")(middleware_auth)

app.include_router(api_router)


@app.get("/")
def root():
    return {
        "app": settings.app_name,
        "version": "0.8.0",
        "status": "online",
        "docs": "/docs"
    }


@app.get("/health")
def health():
    """Endpoint de health check para o Railway saber se estamos vivos."""
    return {"status": "healthy"}