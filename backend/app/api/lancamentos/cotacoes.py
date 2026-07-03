from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from app.api.deps import DbSession
from app.infrastructure.db.models import CotacaoCambio, Ano
from app.schemas.cotacoes import (
    CotacaoCambioCreate, CotacaoCambioUpdate, CotacaoCambioOut,
    AtualizarCotacaoBCB
)
from app.services.conversao_bcb import obter_ou_buscar_cotacao

router = APIRouter(prefix="/cotacoes-cambio", tags=["Apoio - Cotacoes Cambio"])


@router.get("", response_model=list[CotacaoCambioOut])
def listar(
    db: DbSession,
    ano_id: int | None = None,
    mes: int | None = None,
    par: str = "USDBRL",
):
    stmt = select(CotacaoCambio).where(CotacaoCambio.par == par).order_by(
        CotacaoCambio.ano_id.desc(), CotacaoCambio.mes.desc()
    )
    if ano_id: stmt = stmt.where(CotacaoCambio.ano_id == ano_id)
    if mes: stmt = stmt.where(CotacaoCambio.mes == mes)
    return db.scalars(stmt).all()


@router.post("", response_model=CotacaoCambioOut, status_code=status.HTTP_201_CREATED)
def criar(payload: CotacaoCambioCreate, db: DbSession):
    if not db.get(Ano, payload.ano_id):
        raise HTTPException(400, "Ano inválido")
    existe = db.scalar(
        select(CotacaoCambio).where(
            CotacaoCambio.ano_id == payload.ano_id,
            CotacaoCambio.mes == payload.mes,
            CotacaoCambio.par == payload.par,
        )
    )
    if existe:
        raise HTTPException(409, "Já existe cotação para este período")
    obj = CotacaoCambio(**payload.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj


@router.put("/{item_id}", response_model=CotacaoCambioOut)
def atualizar(item_id: int, payload: CotacaoCambioUpdate, db: DbSession):
    obj = db.get(CotacaoCambio, item_id)
    if not obj:
        raise HTTPException(404, "Cotação não encontrada")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit(); db.refresh(obj)
    return obj


@router.post("/atualizar-bcb")
def atualizar_via_bcb(payload: AtualizarCotacaoBCB, db: DbSession):
    """Força atualização da cotação consultando a API do Banco Central."""
    if not db.get(Ano, payload.ano_id):
        raise HTTPException(400, "Ano inválido")
    valor = obter_ou_buscar_cotacao(
        db, payload.ano_id, payload.mes, payload.par, forcar_atualizacao=True
    )
    if not valor:
        raise HTTPException(
            502,
            "Não foi possível obter cotação do BCB. Verifique sua conexão."
        )
    return {"par": payload.par, "ano_id": payload.ano_id, "mes": payload.mes, "cotacao": valor}


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(item_id: int, db: DbSession):
    obj = db.get(CotacaoCambio, item_id)
    if not obj:
        raise HTTPException(404, "Cotação não encontrada")
    db.delete(obj); db.commit()