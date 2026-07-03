from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from app.api.deps import DbSession
from app.infrastructure.db.models import PosicaoAtualAtivo, Ativo
from app.schemas.posicao_atual import (
    PosicaoAtualOut, PrecoMedioManualPayload, PrecoTetoPayload,
    ResultadoAtualizacaoCotacoes, ResultadoRecalculo
)
from app.services.posicao_atual import (
    recalcular_posicao_ativo, recalcular_todas_posicoes,
    definir_preco_medio_manual, voltar_preco_medio_automatico,
    definir_preco_teto, remover_preco_teto,
    _preco_medio_efetivo, calcular_proventos_totais_brl, calcular_custo_total_brl
)
from app.services.cotacoes_externas import atualizar_todas_cotacoes, atualizar_cotacao_via_api

router = APIRouter(prefix="/posicao-atual", tags=["Posicao Atual dos Ativos"])


def _to_out(db, pos: PosicaoAtualAtivo, ativo: Ativo) -> dict:
    preco_medio_efetivo = _preco_medio_efetivo(pos)

    # Rentabilidade (variacao % entre PM e cotacao) - apenas ganho de capital
    rentabilidade = None
    if preco_medio_efetivo and pos.cotacao_atual and preco_medio_efetivo > 0:
        rentabilidade = round(
            (float(pos.cotacao_atual) - preco_medio_efetivo) / preco_medio_efetivo * 100, 2
        )

    # Proventos totais
    proventos_totais = calcular_proventos_totais_brl(db, ativo.id)

    # Custo total em BRL
    custo_total_brl = calcular_custo_total_brl(db, ativo.id)

    # Yield on Cost
    yoc = None
    if proventos_totais > 0 and custo_total_brl > 0:
        yoc = round(proventos_totais / custo_total_brl * 100, 2)

    # 🆕 Rentabilidade TOTAL (capital + proventos)
    # Formula: (Valor Atual + Proventos - Custo) / Custo * 100
    rentabilidade_total = None
    if custo_total_brl > 0 and pos.valor_atual_brl is not None:
        valor_atual = float(pos.valor_atual_brl)
        if valor_atual > 0:
            rentabilidade_total = round(
                ((valor_atual + proventos_totais) - custo_total_brl) / custo_total_brl * 100, 2
            )

    # Margem para aporte
    margem_aporte = None
    acima_do_teto = False
    if pos.preco_teto and pos.cotacao_atual and float(pos.cotacao_atual) > 0:
        teto = float(pos.preco_teto)
        cot = float(pos.cotacao_atual)
        margem_aporte = round((teto - cot) / cot * 100, 2)
        if cot > teto:
            acima_do_teto = True

    return {
        "id": pos.id,
        "ativo_id": pos.ativo_id,
        "ticker": ativo.ticker,
        "nome": ativo.nome,
        "geografia": ativo.geografia,
        "classe": ativo.classe,
        "moeda": ativo.moeda,
        "quantidade": float(pos.quantidade),
        "quantidade_comprada_total": float(pos.quantidade_comprada_total),
        "quantidade_vendida_total": float(pos.quantidade_vendida_total),
        "custo_total": float(pos.custo_total),
        "custo_total_brl": custo_total_brl,
        "preco_medio": preco_medio_efetivo,
        "preco_medio_calculado": float(pos.preco_medio),
        "preco_medio_manual": float(pos.preco_medio_manual) if pos.preco_medio_manual else None,
        "preco_medio_eh_manual": int(pos.preco_medio_eh_manual),
        "cotacao_atual": float(pos.cotacao_atual) if pos.cotacao_atual else None,
        "cotacao_atual_data": pos.cotacao_atual_data,
        "cotacao_fonte": pos.cotacao_fonte,
        "cotacao_usd_brl": float(pos.cotacao_usd_brl) if pos.cotacao_usd_brl else None,
        "valor_atual_brl": float(pos.valor_atual_brl),
        "rentabilidade_pct": rentabilidade,
        "rentabilidade_total_pct": rentabilidade_total,  # 🆕
        "proventos_totais_brl": proventos_totais,
        "yield_on_cost_pct": yoc,
        "preco_teto": float(pos.preco_teto) if pos.preco_teto else None,
        "margem_aporte_pct": margem_aporte,
        "acima_do_teto": acima_do_teto,
    }


@router.get("", response_model=list[PosicaoAtualOut])
def listar(
    db: DbSession,
    apenas_com_posicao: bool = True,
    geografia: str | None = None,
    classe: str | None = None,
):
    stmt = (
        select(PosicaoAtualAtivo, Ativo)
        .join(Ativo, Ativo.id == PosicaoAtualAtivo.ativo_id)
        .order_by(PosicaoAtualAtivo.valor_atual_brl.desc())
    )
    if apenas_com_posicao:
        stmt = stmt.where(PosicaoAtualAtivo.quantidade > 0)
    if geografia:
        stmt = stmt.where(Ativo.geografia == geografia)
    if classe:
        stmt = stmt.where(Ativo.classe == classe)
    rows = db.execute(stmt).all()
    return [_to_out(db, pos, ativo) for pos, ativo in rows]


@router.get("/{ativo_id}", response_model=PosicaoAtualOut)
def obter(ativo_id: int, db: DbSession):
    ativo = db.get(Ativo, ativo_id)
    if not ativo:
        raise HTTPException(404, "Ativo não encontrado")
    pos = db.scalar(select(PosicaoAtualAtivo).where(PosicaoAtualAtivo.ativo_id == ativo_id))
    if not pos:
        raise HTTPException(404, "Posição não encontrada para este ativo")
    return _to_out(db, pos, ativo)


@router.put("/{ativo_id}/preco-medio", response_model=PosicaoAtualOut)
def definir_preco_medio(ativo_id: int, payload: PrecoMedioManualPayload, db: DbSession):
    ativo = db.get(Ativo, ativo_id)
    if not ativo:
        raise HTTPException(404, "Ativo não encontrado")
    try:
        pos = definir_preco_medio_manual(db, ativo_id, payload.preco_medio_manual)
        return _to_out(db, pos, ativo)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/{ativo_id}/voltar-preco-automatico", response_model=PosicaoAtualOut)
def voltar_preco_automatico(ativo_id: int, db: DbSession):
    ativo = db.get(Ativo, ativo_id)
    if not ativo:
        raise HTTPException(404, "Ativo não encontrado")
    try:
        pos = voltar_preco_medio_automatico(db, ativo_id)
        return _to_out(db, pos, ativo)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.put("/{ativo_id}/preco-teto", response_model=PosicaoAtualOut)
def set_preco_teto(ativo_id: int, payload: PrecoTetoPayload, db: DbSession):
    ativo = db.get(Ativo, ativo_id)
    if not ativo:
        raise HTTPException(404, "Ativo não encontrado")
    try:
        pos = definir_preco_teto(db, ativo_id, payload.preco_teto)
        return _to_out(db, pos, ativo)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.delete("/{ativo_id}/preco-teto", response_model=PosicaoAtualOut)
def del_preco_teto(ativo_id: int, db: DbSession):
    ativo = db.get(Ativo, ativo_id)
    if not ativo:
        raise HTTPException(404, "Ativo não encontrado")
    try:
        pos = remover_preco_teto(db, ativo_id)
        return _to_out(db, pos, ativo)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/{ativo_id}/atualizar-cotacao-api", response_model=PosicaoAtualOut)
def atualizar_cotacao_um_ativo(ativo_id: int, db: DbSession):
    from app.services.conversao_bcb import obter_ou_buscar_cotacao
    from datetime import datetime as dt
    from app.infrastructure.db.models import Ano

    ativo = db.get(Ativo, ativo_id)
    if not ativo:
        raise HTTPException(404, "Ativo não encontrado")
    hoje = dt.utcnow()
    ano_obj = db.scalar(select(Ano).where(Ano.ano == hoje.year))
    cotacao_usd_brl = None
    if ano_obj:
        cotacao_usd_brl = obter_ou_buscar_cotacao(db, ano_obj.id, hoje.month)
    r = atualizar_cotacao_via_api(db, ativo, cotacao_usd_brl)
    if not r["ok"] or not r["cotacao"]:
        raise HTTPException(502, f"Não foi possível obter cotação: {r.get('erro', 'erro desconhecido')}")
    db.commit()
    pos = db.scalar(select(PosicaoAtualAtivo).where(PosicaoAtualAtivo.ativo_id == ativo_id))
    return _to_out(db, pos, ativo)


@router.post("/atualizar-cotacoes", response_model=ResultadoAtualizacaoCotacoes)
def atualizar_todas_cotacoes_endpoint(db: DbSession):
    return atualizar_todas_cotacoes(db)


@router.post("/recalcular", response_model=ResultadoRecalculo)
def recalcular(db: DbSession):
    return recalcular_todas_posicoes(db)


@router.post("/{ativo_id}/recalcular", response_model=PosicaoAtualOut)
def recalcular_um(ativo_id: int, db: DbSession):
    ativo = db.get(Ativo, ativo_id)
    if not ativo:
        raise HTTPException(404, "Ativo não encontrado")
    pos = recalcular_posicao_ativo(db, ativo_id)
    return _to_out(db, pos, ativo)