from fastapi import APIRouter, HTTPException
from app.api.deps import DbSession
from app.infrastructure.db.models import Ano
from app.schemas.consolidacao import ConsolidacaoRV, ConsolidacaoPatrimonial
from app.services.consolidacao import (
    consolidar_renda_variavel, consolidar_patrimonial
)

router = APIRouter(prefix="/consolidacao", tags=["Consolidacao Patrimonial"])


@router.get("/renda-variavel", response_model=ConsolidacaoRV)
def consolidacao_rv(db: DbSession, ano_id: int, mes: int):
    """
    M21 — Consolidação de Renda Variável:
    BR + EUA + Cripto agrupados por geografia, classe e ativo.
    """
    if not db.get(Ano, ano_id):
        raise HTTPException(404, "Ano não encontrado")
    if mes < 1 or mes > 12:
        raise HTTPException(400, "Mês inválido")
    try:
        return consolidar_renda_variavel(db, ano_id, mes)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/patrimonial", response_model=ConsolidacaoPatrimonial)
def consolidacao_patrimonial(db: DbSession, ano_id: int, mes: int):
    """
    M22 — Consolidação Patrimonial Total:
    Patrimônio total com componentes, distribuição BRL/USD,
    e variações vs. mês anterior e mesmo mês ano anterior.
    """
    if not db.get(Ano, ano_id):
        raise HTTPException(404, "Ano não encontrado")
    if mes < 1 or mes > 12:
        raise HTTPException(400, "Mês inválido")
    try:
        return consolidar_patrimonial(db, ano_id, mes)
    except ValueError as e:
        raise HTTPException(400, str(e))