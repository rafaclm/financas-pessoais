from fastapi import APIRouter
from app.api.deps import DbSession
from app.schemas.dashboard import DashboardDados
from app.services.dashboard import gerar_dados_dashboard

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/dados", response_model=DashboardDados)
def dados_dashboard(db: DbSession):
    """Retorna todos os dados para renderizar o dashboard principal."""
    return gerar_dados_dashboard(db)