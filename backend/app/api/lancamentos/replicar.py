from fastapi import APIRouter, HTTPException
from app.api.deps import DbSession
from app.infrastructure.db.models import Ano
from app.schemas.replicacao import ReplicarLancamentos, ResultadoReplicacao
from app.services.replicacao import replicar_lancamentos

router = APIRouter(prefix="/lancamentos", tags=["Lancamentos - Replicacao"])


@router.post("/replicar", response_model=ResultadoReplicacao)
def replicar(payload: ReplicarLancamentos, db: DbSession):
    if not db.get(Ano, payload.ano_origem_id):
        raise HTTPException(400, "Ano origem inválido")
    if not db.get(Ano, payload.ano_destino_id):
        raise HTTPException(400, "Ano destino inválido")
    if (payload.ano_origem_id == payload.ano_destino_id
            and payload.mes_origem == payload.mes_destino):
        raise HTTPException(400, "Período origem e destino são iguais")
    return replicar_lancamentos(db, payload)