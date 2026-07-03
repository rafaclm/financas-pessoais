from fastapi import APIRouter
from app.api.deps import DbSession
from app.schemas.balanceamento import AnaliseBalanceamento
from app.services.balanceamento import analisar_balanceamento

router = APIRouter(prefix="/balanceamento", tags=["Balanceamento - Analise"])


@router.get("/analise", response_model=AnaliseBalanceamento)
def analise(db: DbSession):
    """
    Análise de balanceamento da carteira de renda variável.
    Usa a POSIÇÃO ATUAL DOS ATIVOS — sempre atualizada via aportes e cotações.
    Não depende de ano/mês.
    """
    return analisar_balanceamento(db)