from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from app.api.deps import DbSession
from app.infrastructure.db.models import PosicaoAtivoEUA, Ano, Ativo
from app.schemas.posicoes_eua import (
    PosicaoEUACreate, PosicaoEUAUpdate, PosicaoEUAOut
)
from app.schemas.posicoes_br import PrecoMedioSugerido
from app.schemas.posicoes_comum import ReplicarMesAnterior, ResultadoReplicacao
from app.services.posicoes import replicar_posicoes_eua, calcular_preco_medio_sugerido
from app.services.conversao_bcb import obter_ou_buscar_cotacao

router = APIRouter(prefix="/posicoes/ativos-eua", tags=["Posicoes - Ativos EUA"])


def _calcular(db, data: dict) -> dict:
    cot = data.get("cotacao_usd_brl")
    if not cot:
        cot = obter_ou_buscar_cotacao(db, data["ano_id"], data["mes"])
    if not cot:
        raise HTTPException(400, "Cotação USD/BRL não disponível")
    data["cotacao_usd_brl"] = float(cot)
    valor_usd = float(data.get("quantidade", 0)) * float(data.get("cotacao_fechamento_usd", 0))
    data["valor_total_usd"] = valor_usd
    data["valor_total_brl"] = valor_usd * float(cot)
    return data


@router.get("", response_model=list[PosicaoEUAOut])
def listar(db: DbSession, ano_id: int | None = None, mes: int | None = None):
    stmt = select(PosicaoAtivoEUA).order_by(
        PosicaoAtivoEUA.ano_id.desc(), PosicaoAtivoEUA.mes.desc()
    )
    if ano_id: stmt = stmt.where(PosicaoAtivoEUA.ano_id == ano_id)
    if mes: stmt = stmt.where(PosicaoAtivoEUA.mes == mes)
    return db.scalars(stmt).all()


@router.get("/preco-medio-sugerido", response_model=PrecoMedioSugerido)
def preco_medio_sugerido(db: DbSession, ativo_id: int, ano_id: int, mes: int):
    return calcular_preco_medio_sugerido(db, ativo_id, ano_id, mes, moeda_filtro="USD")


@router.post("", response_model=PosicaoEUAOut, status_code=status.HTTP_201_CREATED)
def criar(payload: PosicaoEUACreate, db: DbSession):
    if not db.get(Ano, payload.ano_id):
        raise HTTPException(400, "Ano inválido")
    if not db.get(Ativo, payload.ativo_id):
        raise HTTPException(400, "Ativo inválido")
    existe = db.scalar(select(PosicaoAtivoEUA).where(
        PosicaoAtivoEUA.ano_id == payload.ano_id,
        PosicaoAtivoEUA.mes == payload.mes,
        PosicaoAtivoEUA.ativo_id == payload.ativo_id,
    ))
    if existe:
        raise HTTPException(409, "Já existe posição para este ativo neste período")
    data = _calcular(db, payload.model_dump())
    obj = PosicaoAtivoEUA(**data)
    db.add(obj); db.commit(); db.refresh(obj)
    return obj


@router.post("/lote", response_model=list[PosicaoEUAOut])
def criar_em_lote(payload: list[PosicaoEUACreate], db: DbSession):
    resultados = []
    for item in payload:
        existente = db.scalar(select(PosicaoAtivoEUA).where(
            PosicaoAtivoEUA.ano_id == item.ano_id,
            PosicaoAtivoEUA.mes == item.mes,
            PosicaoAtivoEUA.ativo_id == item.ativo_id,
        ))
        data = _calcular(db, item.model_dump())
        if existente:
            for k, v in data.items():
                setattr(existente, k, v)
            resultados.append(existente)
        else:
            novo = PosicaoAtivoEUA(**data)
            db.add(novo)
            resultados.append(novo)
    db.commit()
    for r in resultados:
        db.refresh(r)
    return resultados


@router.put("/{item_id}", response_model=PosicaoEUAOut)
def atualizar(item_id: int, payload: PosicaoEUAUpdate, db: DbSession):
    obj = db.get(PosicaoAtivoEUA, item_id)
    if not obj:
        raise HTTPException(404, "Não encontrado")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(obj, k, v)
    recalc = _calcular(db, {
        "ano_id": obj.ano_id, "mes": obj.mes, "ativo_id": obj.ativo_id,
        "quantidade": obj.quantidade,
        "cotacao_fechamento_usd": obj.cotacao_fechamento_usd,
        "cotacao_usd_brl": obj.cotacao_usd_brl,
    })
    obj.cotacao_usd_brl = recalc["cotacao_usd_brl"]
    obj.valor_total_usd = recalc["valor_total_usd"]
    obj.valor_total_brl = recalc["valor_total_brl"]
    db.commit(); db.refresh(obj)
    return obj


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(item_id: int, db: DbSession):
    obj = db.get(PosicaoAtivoEUA, item_id)
    if not obj:
        raise HTTPException(404, "Não encontrado")
    db.delete(obj); db.commit()


@router.post("/replicar-mes-anterior", response_model=ResultadoReplicacao)
def replicar(payload: ReplicarMesAnterior, db: DbSession):
    if not db.get(Ano, payload.ano_id):
        raise HTTPException(400, "Ano inválido")
    return replicar_posicoes_eua(db, payload.ano_id, payload.mes, payload.force)