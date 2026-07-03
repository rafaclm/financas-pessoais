from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from app.api.deps import DbSession
from app.infrastructure.db.models import SaldoInvestimento, Ano, ProdutoInvestimento
from app.schemas.saldos_investimentos import (
    SaldoInvestimentoCreate, SaldoInvestimentoUpdate, SaldoInvestimentoOut
)
from app.schemas.posicoes_comum import ReplicarMesAnterior, ResultadoReplicacao
from app.services.posicoes import replicar_saldos_investimentos
from app.services.conversao_bcb import obter_ou_buscar_cotacao

router = APIRouter(prefix="/posicoes/saldos-investimentos",
                   tags=["Posicoes - Saldos Investimentos"])


def _calc_saldo_brl(db, payload_data: dict) -> tuple[float, float | None]:
    produto = db.get(ProdutoInvestimento, payload_data["produto_id"])
    if not produto:
        raise HTTPException(400, "Produto inválido")
    saldo = float(payload_data.get("saldo", 0))
    cot = payload_data.get("cotacao_usd_brl")
    if produto.moeda == "USD":
        if not cot:
            cot = obter_ou_buscar_cotacao(db, payload_data["ano_id"], payload_data["mes"])
        if not cot:
            raise HTTPException(400, "Cotação USD/BRL não disponível")
        return saldo * float(cot), float(cot)
    return saldo, None


@router.get("", response_model=list[SaldoInvestimentoOut])
def listar(db: DbSession, ano_id: int | None = None, mes: int | None = None):
    stmt = select(SaldoInvestimento).order_by(
        SaldoInvestimento.ano_id.desc(), SaldoInvestimento.mes.desc()
    )
    if ano_id: stmt = stmt.where(SaldoInvestimento.ano_id == ano_id)
    if mes: stmt = stmt.where(SaldoInvestimento.mes == mes)
    return db.scalars(stmt).all()


@router.post("", response_model=SaldoInvestimentoOut, status_code=status.HTTP_201_CREATED)
def criar(payload: SaldoInvestimentoCreate, db: DbSession):
    if not db.get(Ano, payload.ano_id):
        raise HTTPException(400, "Ano inválido")
    existe = db.scalar(select(SaldoInvestimento).where(
        SaldoInvestimento.ano_id == payload.ano_id,
        SaldoInvestimento.mes == payload.mes,
        SaldoInvestimento.produto_id == payload.produto_id,
    ))
    if existe:
        raise HTTPException(409, "Já existe saldo para este produto neste período")

    data = payload.model_dump()
    saldo_brl, cot = _calc_saldo_brl(db, data)
    data["saldo_brl"] = saldo_brl
    data["cotacao_usd_brl"] = cot
    obj = SaldoInvestimento(**data)
    db.add(obj); db.commit(); db.refresh(obj)
    return obj


@router.post("/lote", response_model=list[SaldoInvestimentoOut])
def criar_em_lote(payload: list[SaldoInvestimentoCreate], db: DbSession):
    resultados = []
    for item in payload:
        if not db.get(Ano, item.ano_id):
            raise HTTPException(400, f"Ano {item.ano_id} inválido")
        existente = db.scalar(select(SaldoInvestimento).where(
            SaldoInvestimento.ano_id == item.ano_id,
            SaldoInvestimento.mes == item.mes,
            SaldoInvestimento.produto_id == item.produto_id,
        ))
        data = item.model_dump()
        saldo_brl, cot = _calc_saldo_brl(db, data)
        if existente:
            existente.saldo = data["saldo"]
            existente.cotacao_usd_brl = cot
            existente.saldo_brl = saldo_brl
            resultados.append(existente)
        else:
            data["saldo_brl"] = saldo_brl
            data["cotacao_usd_brl"] = cot
            novo = SaldoInvestimento(**data)
            db.add(novo)
            resultados.append(novo)
    db.commit()
    for r in resultados:
        db.refresh(r)
    return resultados


@router.put("/{item_id}", response_model=SaldoInvestimentoOut)
def atualizar(item_id: int, payload: SaldoInvestimentoUpdate, db: DbSession):
    obj = db.get(SaldoInvestimento, item_id)
    if not obj:
        raise HTTPException(404, "Não encontrado")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(obj, k, v)
    saldo_brl, cot = _calc_saldo_brl(db, {
        "produto_id": obj.produto_id, "ano_id": obj.ano_id, "mes": obj.mes,
        "saldo": obj.saldo, "cotacao_usd_brl": obj.cotacao_usd_brl,
    })
    obj.saldo_brl = saldo_brl
    obj.cotacao_usd_brl = cot
    db.commit(); db.refresh(obj)
    return obj


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(item_id: int, db: DbSession):
    obj = db.get(SaldoInvestimento, item_id)
    if not obj:
        raise HTTPException(404, "Não encontrado")
    db.delete(obj); db.commit()


@router.post("/replicar-mes-anterior", response_model=ResultadoReplicacao)
def replicar(payload: ReplicarMesAnterior, db: DbSession):
    if not db.get(Ano, payload.ano_id):
        raise HTTPException(400, "Ano inválido")
    return replicar_saldos_investimentos(db, payload.ano_id, payload.mes, payload.force)