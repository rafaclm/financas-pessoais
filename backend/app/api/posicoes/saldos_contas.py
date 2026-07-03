from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from app.api.deps import DbSession
from app.infrastructure.db.models import SaldoConta, Ano, Conta
from app.schemas.saldos_contas import (
    SaldoContaCreate, SaldoContaUpdate, SaldoContaOut
)
from app.schemas.posicoes_comum import ReplicarMesAnterior, ResultadoReplicacao
from app.services.posicoes import replicar_saldos_contas
from app.services.conversao_bcb import obter_ou_buscar_cotacao

router = APIRouter(prefix="/posicoes/saldos-contas", tags=["Posicoes - Saldos Contas"])


def _calc_saldo_brl(db, payload_data: dict) -> tuple[float, float | None]:
    """Calcula saldo_brl conforme moeda da conta. Retorna (saldo_brl, cotacao_usada)."""
    conta = db.get(Conta, payload_data["conta_id"])
    if not conta:
        raise HTTPException(400, "Conta inválida")
    saldo = float(payload_data.get("saldo", 0))
    cot = payload_data.get("cotacao_usd_brl")
    if conta.moeda == "USD":
        if not cot:
            cot = obter_ou_buscar_cotacao(db, payload_data["ano_id"], payload_data["mes"])
        if not cot:
            raise HTTPException(400, "Cotação USD/BRL não disponível")
        return saldo * float(cot), float(cot)
    return saldo, None


@router.get("", response_model=list[SaldoContaOut])
def listar(db: DbSession, ano_id: int | None = None, mes: int | None = None):
    stmt = select(SaldoConta).order_by(SaldoConta.ano_id.desc(), SaldoConta.mes.desc())
    if ano_id: stmt = stmt.where(SaldoConta.ano_id == ano_id)
    if mes: stmt = stmt.where(SaldoConta.mes == mes)
    return db.scalars(stmt).all()


@router.post("", response_model=SaldoContaOut, status_code=status.HTTP_201_CREATED)
def criar(payload: SaldoContaCreate, db: DbSession):
    if not db.get(Ano, payload.ano_id):
        raise HTTPException(400, "Ano inválido")
    # Verifica duplicidade
    existe = db.scalar(select(SaldoConta).where(
        SaldoConta.ano_id == payload.ano_id,
        SaldoConta.mes == payload.mes,
        SaldoConta.conta_id == payload.conta_id,
    ))
    if existe:
        raise HTTPException(409, "Já existe saldo para esta conta neste período")

    data = payload.model_dump()
    saldo_brl, cot = _calc_saldo_brl(db, data)
    data["saldo_brl"] = saldo_brl
    data["cotacao_usd_brl"] = cot
    obj = SaldoConta(**data)
    db.add(obj); db.commit(); db.refresh(obj)
    return obj


@router.post("/lote", response_model=list[SaldoContaOut])
def criar_em_lote(payload: list[SaldoContaCreate], db: DbSession):
    """Upsert em lote: cria ou atualiza saldos."""
    resultados = []
    for item in payload:
        if not db.get(Ano, item.ano_id):
            raise HTTPException(400, f"Ano {item.ano_id} inválido")
        existente = db.scalar(select(SaldoConta).where(
            SaldoConta.ano_id == item.ano_id,
            SaldoConta.mes == item.mes,
            SaldoConta.conta_id == item.conta_id,
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
            novo = SaldoConta(**data)
            db.add(novo)
            resultados.append(novo)
    db.commit()
    for r in resultados:
        db.refresh(r)
    return resultados


@router.put("/{item_id}", response_model=SaldoContaOut)
def atualizar(item_id: int, payload: SaldoContaUpdate, db: DbSession):
    obj = db.get(SaldoConta, item_id)
    if not obj:
        raise HTTPException(404, "Saldo não encontrado")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(obj, k, v)
    saldo_brl, cot = _calc_saldo_brl(db, {
        "conta_id": obj.conta_id, "ano_id": obj.ano_id, "mes": obj.mes,
        "saldo": obj.saldo, "cotacao_usd_brl": obj.cotacao_usd_brl,
    })
    obj.saldo_brl = saldo_brl
    obj.cotacao_usd_brl = cot
    db.commit(); db.refresh(obj)
    return obj


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(item_id: int, db: DbSession):
    obj = db.get(SaldoConta, item_id)
    if not obj:
        raise HTTPException(404, "Saldo não encontrado")
    db.delete(obj); db.commit()


@router.post("/replicar-mes-anterior", response_model=ResultadoReplicacao)
def replicar(payload: ReplicarMesAnterior, db: DbSession):
    if not db.get(Ano, payload.ano_id):
        raise HTTPException(400, "Ano inválido")
    return replicar_saldos_contas(db, payload.ano_id, payload.mes, payload.force)