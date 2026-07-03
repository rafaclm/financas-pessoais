from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select, func
from app.api.deps import DbSession
from app.infrastructure.db.models import Provento, Ano, Ativo, Conta
from app.schemas.proventos import ProventoCreate, ProventoUpdate, ProventoOut
from app.schemas.resumos_invest import (
    ResumoMensalProventos, ResumoProventosPorAtivo, ResumoAnualProventos
)
from app.services.conversao_bcb import obter_ou_buscar_cotacao


def _converter(db, payload, atual: Provento | None = None):
    moeda = payload.moeda if payload.moeda is not None else (atual.moeda if atual else "BRL")
    valor_liq = payload.valor_liquido if payload.valor_liquido is not None else (atual.valor_liquido if atual else 0)
    ano_id = payload.ano_id if payload.ano_id is not None else (atual.ano_id if atual else None)
    mes = payload.mes if payload.mes is not None else (atual.mes if atual else None)

    cotacao = None
    if moeda == "USD":
        cotacao = payload.cotacao_usd_brl
        if not cotacao:
            cotacao = obter_ou_buscar_cotacao(db, ano_id, mes)
        if not cotacao:
            raise HTTPException(400, "Não foi possível obter cotação USD/BRL.")
        valor_liq_brl = float(valor_liq) * float(cotacao)
    else:
        valor_liq_brl = float(valor_liq)

    return valor_liq_brl, cotacao


router = APIRouter(prefix="/proventos", tags=["Lancamentos - Proventos"])


@router.get("", response_model=list[ProventoOut])
def listar(
    db: DbSession,
    ano_id: int | None = None,
    mes: int | None = None,
    ativo_id: int | None = None,
    tipo: str | None = None,
):
    stmt = select(Provento).order_by(
        Provento.data.desc(), Provento.id.desc()
    )
    if ano_id: stmt = stmt.where(Provento.ano_id == ano_id)
    if mes: stmt = stmt.where(Provento.mes == mes)
    if ativo_id: stmt = stmt.where(Provento.ativo_id == ativo_id)
    if tipo: stmt = stmt.where(Provento.tipo == tipo)
    return db.scalars(stmt).all()


@router.get("/resumo-mensal", response_model=list[ResumoMensalProventos])
def resumo_mensal(db: DbSession, ano_id: int):
    """Totais mensais de proventos no ano."""
    rows = db.execute(
        select(
            Provento.mes,
            func.coalesce(func.sum(Provento.valor_liquido_brl), 0).label("total_brl"),
            func.count(Provento.id).label("qtd"),
        )
        .where(Provento.ano_id == ano_id)
        .group_by(Provento.mes)
        .order_by(Provento.mes)
    ).all()
    return [
        ResumoMensalProventos(
            mes=r.mes,
            total_brl=float(r.total_brl or 0),
            qtd=r.qtd,
        )
        for r in rows
    ]


@router.get("/resumo-anual", response_model=ResumoAnualProventos)
def resumo_anual(db: DbSession, ano_id: int):
    """Resumo consolidado do ano: total acumulado, média mensal, maior mês."""
    rows = db.execute(
        select(
            Provento.mes,
            func.coalesce(func.sum(Provento.valor_liquido_brl), 0).label("total_brl"),
            func.count(Provento.id).label("qtd"),
        )
        .where(Provento.ano_id == ano_id)
        .group_by(Provento.mes)
    ).all()

    total_acumulado = sum(float(r.total_brl) for r in rows)
    qtd_total = sum(r.qtd for r in rows)
    meses_com_dados = len(rows)
    media_mensal = total_acumulado / meses_com_dados if meses_com_dados > 0 else 0

    maior_mes = None
    maior_valor = 0.0
    for r in rows:
        if float(r.total_brl) > maior_valor:
            maior_valor = float(r.total_brl)
            maior_mes = r.mes

    return ResumoAnualProventos(
        total_acumulado_brl=total_acumulado,
        media_mensal_brl=media_mensal,
        maior_mes=maior_mes,
        maior_valor=maior_valor,
        qtd_total=qtd_total,
    )


@router.get("/por-ativo", response_model=list[ResumoProventosPorAtivo])
def por_ativo(db: DbSession, ano_id: int):
    """Total recebido por ativo no ano."""
    rows = db.execute(
        select(
            Provento.ativo_id,
            Ativo.ticker,
            Ativo.nome,
            func.count(Provento.id).label("qtd"),
            func.coalesce(func.sum(Provento.valor_liquido_brl), 0).label("total_brl"),
        )
        .join(Ativo, Ativo.id == Provento.ativo_id)
        .where(Provento.ano_id == ano_id)
        .group_by(Provento.ativo_id, Ativo.ticker, Ativo.nome)
        .order_by(func.sum(Provento.valor_liquido_brl).desc())
    ).all()
    return [
        ResumoProventosPorAtivo(
            ativo_id=r.ativo_id, ticker=r.ticker, nome=r.nome,
            qtd=r.qtd, total_brl=float(r.total_brl or 0),
        )
        for r in rows
    ]


@router.get("/{item_id}", response_model=ProventoOut)
def obter(item_id: int, db: DbSession):
    obj = db.get(Provento, item_id)
    if not obj:
        raise HTTPException(404, "Provento não encontrado")
    return obj


@router.post("", response_model=ProventoOut, status_code=status.HTTP_201_CREATED)
def criar(payload: ProventoCreate, db: DbSession):
    if not db.get(Ano, payload.ano_id):
        raise HTTPException(400, "Ano inválido")
    if not db.get(Ativo, payload.ativo_id):
        raise HTTPException(400, "Ativo inválido")
    if payload.conta_id and not db.get(Conta, payload.conta_id):
        raise HTTPException(400, "Conta inválida")

    valor_liq_brl, cotacao = _converter(db, payload)
    data = payload.model_dump()
    data["valor_liquido_brl"] = valor_liq_brl
    if data["moeda"] == "USD":
        data["cotacao_usd_brl"] = cotacao
    else:
        data["cotacao_usd_brl"] = None
    obj = Provento(**data)
    db.add(obj); db.commit(); db.refresh(obj)
    return obj


@router.put("/{item_id}", response_model=ProventoOut)
def atualizar(item_id: int, payload: ProventoUpdate, db: DbSession):
    obj = db.get(Provento, item_id)
    if not obj:
        raise HTTPException(404, "Provento não encontrado")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(obj, k, v)
    valor_liq_brl, cotacao = _converter(db, payload, obj)
    obj.valor_liquido_brl = valor_liq_brl
    if obj.moeda == "USD":
        obj.cotacao_usd_brl = cotacao
    else:
        obj.cotacao_usd_brl = None
    db.commit(); db.refresh(obj)
    return obj


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(item_id: int, db: DbSession):
    obj = db.get(Provento, item_id)
    if not obj:
        raise HTTPException(404, "Provento não encontrado")
    db.delete(obj); db.commit()