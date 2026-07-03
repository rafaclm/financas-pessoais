from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from app.api.deps import DbSession
from app.infrastructure.db.models import PosicaoAtivoBR, Ano, Ativo
from app.schemas.posicoes_br import (
    PosicaoBRCreate, PosicaoBRUpdate, PosicaoBROut, PrecoMedioSugerido
)
from app.schemas.posicoes_comum import ReplicarMesAnterior, ResultadoReplicacao
from app.services.posicoes import replicar_posicoes_br, calcular_preco_medio_sugerido

router = APIRouter(prefix="/posicoes/ativos-br", tags=["Posicoes - Ativos BR"])


def _calcular(data: dict) -> dict:
    data["valor_total"] = float(data.get("quantidade", 0)) * float(data.get("cotacao_fechamento", 0))
    return data


@router.get("", response_model=list[PosicaoBROut])
def listar(db: DbSession, ano_id: int | None = None, mes: int | None = None):
    stmt = select(PosicaoAtivoBR).order_by(
        PosicaoAtivoBR.ano_id.desc(), PosicaoAtivoBR.mes.desc()
    )
    if ano_id: stmt = stmt.where(PosicaoAtivoBR.ano_id == ano_id)
    if mes: stmt = stmt.where(PosicaoAtivoBR.mes == mes)
    return db.scalars(stmt).all()


@router.get("/preco-medio-sugerido", response_model=PrecoMedioSugerido)
def preco_medio_sugerido(db: DbSession, ativo_id: int, ano_id: int, mes: int):
    return calcular_preco_medio_sugerido(db, ativo_id, ano_id, mes, moeda_filtro="BRL")


@router.post("", response_model=PosicaoBROut, status_code=status.HTTP_201_CREATED)
def criar(payload: PosicaoBRCreate, db: DbSession):
    if not db.get(Ano, payload.ano_id):
        raise HTTPException(400, "Ano inválido")
    if not db.get(Ativo, payload.ativo_id):
        raise HTTPException(400, "Ativo inválido")
    existe = db.scalar(select(PosicaoAtivoBR).where(
        PosicaoAtivoBR.ano_id == payload.ano_id,
        PosicaoAtivoBR.mes == payload.mes,
        PosicaoAtivoBR.ativo_id == payload.ativo_id,
    ))
    if existe:
        raise HTTPException(409, "Já existe posição para este ativo neste período")
    data = _calcular(payload.model_dump())
    obj = PosicaoAtivoBR(**data)
    db.add(obj); db.commit(); db.refresh(obj)
    return obj


@router.post("/lote", response_model=list[PosicaoBROut])
def criar_em_lote(payload: list[PosicaoBRCreate], db: DbSession):
    resultados = []
    for item in payload:
        existente = db.scalar(select(PosicaoAtivoBR).where(
            PosicaoAtivoBR.ano_id == item.ano_id,
            PosicaoAtivoBR.mes == item.mes,
            PosicaoAtivoBR.ativo_id == item.ativo_id,
        ))
        data = _calcular(item.model_dump())
        if existente:
            for k, v in data.items():
                setattr(existente, k, v)
            resultados.append(existente)
        else:
            novo = PosicaoAtivoBR(**data)
            db.add(novo)
            resultados.append(novo)
    db.commit()
    for r in resultados:
        db.refresh(r)
    return resultados


@router.put("/{item_id}", response_model=PosicaoBROut)
def atualizar(item_id: int, payload: PosicaoBRUpdate, db: DbSession):
    obj = db.get(PosicaoAtivoBR, item_id)
    if not obj:
        raise HTTPException(404, "Não encontrado")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(obj, k, v)
    obj.valor_total = float(obj.quantidade) * float(obj.cotacao_fechamento)
    db.commit(); db.refresh(obj)
    return obj


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(item_id: int, db: DbSession):
    obj = db.get(PosicaoAtivoBR, item_id)
    if not obj:
        raise HTTPException(404, "Não encontrado")
    db.delete(obj); db.commit()


@router.post("/replicar-mes-anterior", response_model=ResultadoReplicacao)
def replicar(payload: ReplicarMesAnterior, db: DbSession):
    if not db.get(Ano, payload.ano_id):
        raise HTTPException(400, "Ano inválido")
    return replicar_posicoes_br(db, payload.ano_id, payload.mes, payload.force)