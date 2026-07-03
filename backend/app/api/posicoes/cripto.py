from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from app.api.deps import DbSession
from app.infrastructure.db.models import PosicaoCripto, Ano, Ativo
from app.schemas.posicoes_cripto import (
    PosicaoCriptoCreate, PosicaoCriptoUpdate, PosicaoCriptoOut
)
from app.schemas.posicoes_comum import ReplicarMesAnterior, ResultadoReplicacao
from app.services.posicoes import replicar_posicoes_cripto, _mes_anterior
from app.services.conversao_bcb import obter_ou_buscar_cotacao

router = APIRouter(prefix="/posicoes/cripto", tags=["Posicoes - Criptoativos"])


def _calcular(db, data: dict) -> dict:
    """Calcula saldo_usd e variacao_pct."""
    cot = data.get("cotacao_usd_brl")
    if not cot:
        cot = obter_ou_buscar_cotacao(db, data["ano_id"], data["mes"])
    if not cot:
        raise HTTPException(400, "Cotação USD/BRL não disponível")
    data["cotacao_usd_brl"] = float(cot)
    saldo_brl = float(data.get("saldo_brl", 0))
    data["saldo_usd"] = saldo_brl / float(cot) if cot else 0

    # Variação vs. mês anterior
    ano_ant, mes_ant = _mes_anterior(db, data["ano_id"], data["mes"])
    if ano_ant:
        anterior = db.scalar(select(PosicaoCripto).where(
            PosicaoCripto.ano_id == ano_ant,
            PosicaoCripto.mes == mes_ant,
            PosicaoCripto.ativo_id == data["ativo_id"],
        ))
        if anterior and float(anterior.saldo_brl) > 0:
            data["variacao_pct"] = round(
                (saldo_brl - float(anterior.saldo_brl)) / float(anterior.saldo_brl) * 100, 4
            )
        else:
            data["variacao_pct"] = None
    else:
        data["variacao_pct"] = None
    return data


@router.get("", response_model=list[PosicaoCriptoOut])
def listar(db: DbSession, ano_id: int | None = None, mes: int | None = None):
    stmt = select(PosicaoCripto).order_by(
        PosicaoCripto.ano_id.desc(), PosicaoCripto.mes.desc()
    )
    if ano_id: stmt = stmt.where(PosicaoCripto.ano_id == ano_id)
    if mes: stmt = stmt.where(PosicaoCripto.mes == mes)
    return db.scalars(stmt).all()


@router.post("", response_model=PosicaoCriptoOut, status_code=status.HTTP_201_CREATED)
def criar(payload: PosicaoCriptoCreate, db: DbSession):
    if not db.get(Ano, payload.ano_id):
        raise HTTPException(400, "Ano inválido")
    if not db.get(Ativo, payload.ativo_id):
        raise HTTPException(400, "Ativo inválido")
    existe = db.scalar(select(PosicaoCripto).where(
        PosicaoCripto.ano_id == payload.ano_id,
        PosicaoCripto.mes == payload.mes,
        PosicaoCripto.ativo_id == payload.ativo_id,
    ))
    if existe:
        raise HTTPException(409, "Já existe posição para este ativo neste período")
    data = _calcular(db, payload.model_dump())
    obj = PosicaoCripto(**data)
    db.add(obj); db.commit(); db.refresh(obj)
    return obj


@router.post("/lote", response_model=list[PosicaoCriptoOut])
def criar_em_lote(payload: list[PosicaoCriptoCreate], db: DbSession):
    resultados = []
    for item in payload:
        existente = db.scalar(select(PosicaoCripto).where(
            PosicaoCripto.ano_id == item.ano_id,
            PosicaoCripto.mes == item.mes,
            PosicaoCripto.ativo_id == item.ativo_id,
        ))
        data = _calcular(db, item.model_dump())
        if existente:
            for k, v in data.items():
                setattr(existente, k, v)
            resultados.append(existente)
        else:
            novo = PosicaoCripto(**data)
            db.add(novo)
            resultados.append(novo)
    db.commit()
    for r in resultados:
        db.refresh(r)
    return resultados


@router.put("/{item_id}", response_model=PosicaoCriptoOut)
def atualizar(item_id: int, payload: PosicaoCriptoUpdate, db: DbSession):
    obj = db.get(PosicaoCripto, item_id)
    if not obj:
        raise HTTPException(404, "Não encontrado")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(obj, k, v)
    recalc = _calcular(db, {
        "ano_id": obj.ano_id, "mes": obj.mes, "ativo_id": obj.ativo_id,
        "quantidade": obj.quantidade, "saldo_brl": obj.saldo_brl,
        "cotacao_usd_brl": obj.cotacao_usd_brl,
    })
    obj.saldo_usd = recalc["saldo_usd"]
    obj.cotacao_usd_brl = recalc["cotacao_usd_brl"]
    obj.variacao_pct = recalc["variacao_pct"]
    db.commit(); db.refresh(obj)
    return obj


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(item_id: int, db: DbSession):
    obj = db.get(PosicaoCripto, item_id)
    if not obj:
        raise HTTPException(404, "Não encontrado")
    db.delete(obj); db.commit()


@router.post("/replicar-mes-anterior", response_model=ResultadoReplicacao)
def replicar(payload: ReplicarMesAnterior, db: DbSession):
    if not db.get(Ano, payload.ano_id):
        raise HTTPException(400, "Ano inválido")
    return replicar_posicoes_cripto(db, payload.ano_id, payload.mes, payload.force)