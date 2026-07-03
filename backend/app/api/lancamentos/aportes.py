from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select, func, case
from app.api.deps import DbSession
from app.infrastructure.db.models import AporteBolsa, Ano, Ativo, Conta
from app.schemas.aportes import AporteCreate, AporteUpdate, AporteOut
from app.schemas.resumos_invest import ResumoMensalAportes, ResumoPorAtivo
from app.services.conversao_bcb import obter_ou_buscar_cotacao
from app.services.posicao_atual import recalcular_posicao_ativo


def _validar_e_calcular(db, payload, atual: AporteBolsa | None = None):
    if payload.ano_id and not db.get(Ano, payload.ano_id):
        raise HTTPException(400, "Ano inválido")
    if payload.ativo_id and not db.get(Ativo, payload.ativo_id):
        raise HTTPException(400, "Ativo inválido")
    if payload.conta_id and not db.get(Conta, payload.conta_id):
        raise HTTPException(400, "Conta inválida")

    qtd = payload.quantidade if payload.quantidade is not None else (atual.quantidade if atual else 0)
    preco = payload.preco_unitario if payload.preco_unitario is not None else (atual.preco_unitario if atual else 0)
    taxas = payload.taxas if payload.taxas is not None else (atual.taxas if atual else 0)
    moeda = payload.moeda if payload.moeda is not None else (atual.moeda if atual else "BRL")
    ano_id = payload.ano_id if payload.ano_id is not None else (atual.ano_id if atual else None)
    mes = payload.mes if payload.mes is not None else (atual.mes if atual else None)

    valor_total = float(qtd) * float(preco) + float(taxas)

    cotacao = None
    if moeda == "USD":
        cotacao = payload.cotacao_usd_brl
        if not cotacao:
            cotacao = obter_ou_buscar_cotacao(db, ano_id, mes)
        if not cotacao:
            raise HTTPException(
                400,
                "Não foi possível obter cotação USD/BRL. "
                "Verifique sua conexão ou cadastre manualmente em /cotacoes-cambio."
            )
        valor_total_brl = valor_total * float(cotacao)
    else:
        valor_total_brl = valor_total

    return valor_total, valor_total_brl, cotacao


router = APIRouter(prefix="/aportes", tags=["Lancamentos - Aportes"])


@router.get("", response_model=list[AporteOut])
def listar(
    db: DbSession,
    ano_id: int | None = None,
    mes: int | None = None,
    ativo_id: int | None = None,
    tipo_operacao: str | None = None,
):
    stmt = select(AporteBolsa).order_by(
        AporteBolsa.data.desc(),
        AporteBolsa.id.desc(),
    )
    if ano_id: stmt = stmt.where(AporteBolsa.ano_id == ano_id)
    if mes: stmt = stmt.where(AporteBolsa.mes == mes)
    if ativo_id: stmt = stmt.where(AporteBolsa.ativo_id == ativo_id)
    if tipo_operacao: stmt = stmt.where(AporteBolsa.tipo_operacao == tipo_operacao)
    return db.scalars(stmt).all()


@router.get("/resumo-mensal", response_model=list[ResumoMensalAportes])
def resumo_mensal(db: DbSession, ano_id: int):
    rows = db.execute(
        select(
            AporteBolsa.mes,
            func.coalesce(func.sum(AporteBolsa.valor_total_brl), 0).label("total_brl"),
            func.count(AporteBolsa.id).label("qtd"),
            func.sum(
                case((AporteBolsa.tipo_operacao == "compra", 1), else_=0)
            ).label("qtd_compras"),
            func.sum(
                case((AporteBolsa.tipo_operacao == "venda", 1), else_=0)
            ).label("qtd_vendas"),
            func.coalesce(func.sum(
                case((AporteBolsa.tipo_operacao == "compra", AporteBolsa.valor_total_brl), else_=0)
            ), 0).label("total_compras"),
            func.coalesce(func.sum(
                case((AporteBolsa.tipo_operacao == "venda", AporteBolsa.valor_total_brl), else_=0)
            ), 0).label("total_vendas"),
        )
        .where(AporteBolsa.ano_id == ano_id)
        .group_by(AporteBolsa.mes)
        .order_by(AporteBolsa.mes)
    ).all()
    return [
        ResumoMensalAportes(
            mes=r.mes,
            total_brl=float(r.total_brl or 0),
            qtd_operacoes=r.qtd,
            qtd_compras=int(r.qtd_compras or 0),
            qtd_vendas=int(r.qtd_vendas or 0),
            total_compras_brl=float(r.total_compras or 0),
            total_vendas_brl=float(r.total_vendas or 0),
        )
        for r in rows
    ]


@router.get("/por-ativo", response_model=list[ResumoPorAtivo])
def resumo_por_ativo(db: DbSession, ano_id: int, tipo_operacao: str | None = None):
    stmt = (
        select(
            AporteBolsa.ativo_id,
            Ativo.ticker,
            Ativo.nome,
            func.sum(AporteBolsa.valor_total_brl).label("total_brl"),
            func.count(AporteBolsa.id).label("qtd_operacoes"),
            func.sum(AporteBolsa.quantidade).label("qtd_acumulada"),
        )
        .join(Ativo, Ativo.id == AporteBolsa.ativo_id)
        .where(AporteBolsa.ano_id == ano_id)
        .group_by(AporteBolsa.ativo_id, Ativo.ticker, Ativo.nome)
        .order_by(func.sum(AporteBolsa.valor_total_brl).desc())
    )
    if tipo_operacao:
        stmt = stmt.where(AporteBolsa.tipo_operacao == tipo_operacao)
    rows = db.execute(stmt).all()
    return [
        ResumoPorAtivo(
            ativo_id=r.ativo_id, ticker=r.ticker, nome=r.nome,
            qtd_operacoes=r.qtd_operacoes,
            total_brl=float(r.total_brl or 0),
            quantidade_acumulada=float(r.qtd_acumulada or 0),
        )
        for r in rows
    ]


@router.get("/{item_id}", response_model=AporteOut)
def obter(item_id: int, db: DbSession):
    obj = db.get(AporteBolsa, item_id)
    if not obj:
        raise HTTPException(404, "Aporte não encontrado")
    return obj


@router.post("", response_model=AporteOut, status_code=status.HTTP_201_CREATED)
def criar(payload: AporteCreate, db: DbSession):
    valor_total, valor_total_brl, cotacao = _validar_e_calcular(db, payload)
    data = payload.model_dump()
    data["valor_total"] = valor_total
    data["valor_total_brl"] = valor_total_brl
    if data["moeda"] == "USD":
        data["cotacao_usd_brl"] = cotacao
    else:
        data["cotacao_usd_brl"] = None
    obj = AporteBolsa(**data)
    db.add(obj); db.commit(); db.refresh(obj)

    # 🪄 HOOK AUTOMÁTICO: recalcula posição atual deste ativo
    try:
        recalcular_posicao_ativo(db, obj.ativo_id)
    except Exception:
        pass  # falha silenciosa no recálculo não bloqueia o aporte

    return obj


@router.put("/{item_id}", response_model=AporteOut)
def atualizar(item_id: int, payload: AporteUpdate, db: DbSession):
    obj = db.get(AporteBolsa, item_id)
    if not obj:
        raise HTTPException(404, "Aporte não encontrado")
    ativo_id_anterior = obj.ativo_id
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(obj, k, v)
    valor_total, valor_total_brl, cotacao = _validar_e_calcular(db, payload, obj)
    obj.valor_total = valor_total
    obj.valor_total_brl = valor_total_brl
    if obj.moeda == "USD":
        obj.cotacao_usd_brl = cotacao
    else:
        obj.cotacao_usd_brl = None
    db.commit(); db.refresh(obj)

    # 🪄 HOOK: recalcula ativo atual + ativo anterior (se trocou)
    try:
        recalcular_posicao_ativo(db, obj.ativo_id)
        if obj.ativo_id != ativo_id_anterior:
            recalcular_posicao_ativo(db, ativo_id_anterior)
    except Exception:
        pass

    return obj


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(item_id: int, db: DbSession):
    obj = db.get(AporteBolsa, item_id)
    if not obj:
        raise HTTPException(404, "Aporte não encontrado")
    ativo_id = obj.ativo_id
    db.delete(obj); db.commit()

    # 🪄 HOOK: recalcula posição do ativo após remoção
    try:
        recalcular_posicao_ativo(db, ativo_id)
    except Exception:
        pass