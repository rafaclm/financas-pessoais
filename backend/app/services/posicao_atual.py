"""
Service de Posição Atual dos Ativos.
- Calcula posição a partir dos aportes
- Preserva preço médio manual
- Calcula proventos totais por ativo
- Suporta preço teto manual
"""
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.infrastructure.db.models import (
    PosicaoAtualAtivo, AporteBolsa, Ativo, Provento
)


def _preco_medio_efetivo(pos: PosicaoAtualAtivo) -> float:
    if pos.preco_medio_eh_manual and pos.preco_medio_manual:
        return float(pos.preco_medio_manual)
    return float(pos.preco_medio)


def calcular_custo_total_brl(db: Session, ativo_id: int) -> float:
    """Soma total investido em BRL (compras) considerando cotação USD do momento."""
    rows = db.execute(
        select(
            AporteBolsa.quantidade,
            AporteBolsa.preco_unitario,
            AporteBolsa.taxas,
            AporteBolsa.moeda,
            AporteBolsa.cotacao_usd_brl,
            AporteBolsa.valor_total_brl,
        )
        .where(
            AporteBolsa.ativo_id == ativo_id,
            AporteBolsa.tipo_operacao == "compra",
        )
    ).all()
    # Já temos valor_total_brl calculado no aporte (inclui taxas e câmbio)
    return round(sum(float(r.valor_total_brl) for r in rows), 4)


def calcular_proventos_totais_brl(db: Session, ativo_id: int) -> float:
    """Soma de todos os proventos recebidos do ativo (em BRL)."""
    total = db.scalar(
        select(func.coalesce(func.sum(Provento.valor_liquido_brl), 0))
        .where(Provento.ativo_id == ativo_id)
    ) or 0
    return round(float(total), 2)


def recalcular_posicao_ativo(db: Session, ativo_id: int, commit: bool = True) -> PosicaoAtualAtivo:
    """Recalcula a posição de UM ativo com base em todos os aportes."""
    ativo = db.get(Ativo, ativo_id)
    if not ativo:
        raise ValueError(f"Ativo {ativo_id} não encontrado")

    aportes = db.scalars(
        select(AporteBolsa)
        .where(AporteBolsa.ativo_id == ativo_id)
        .order_by(AporteBolsa.data, AporteBolsa.id)
    ).all()

    qtd_comprada = 0.0
    qtd_vendida = 0.0
    custo_total = 0.0  # na moeda nativa

    for ap in aportes:
        qtd = float(ap.quantidade)
        preco = float(ap.preco_unitario)
        if ap.tipo_operacao == "compra":
            qtd_comprada += qtd
            custo_total += qtd * preco
        else:
            qtd_vendida += qtd

    qtd_liquida = qtd_comprada - qtd_vendida
    preco_medio_calc = (custo_total / qtd_comprada) if qtd_comprada > 0 else 0

    pos = db.scalar(select(PosicaoAtualAtivo).where(PosicaoAtualAtivo.ativo_id == ativo_id))
    cotacao_atual_preservada = pos.cotacao_atual if pos else None
    cotacao_data_preservada = pos.cotacao_atual_data if pos else None
    cotacao_fonte_preservada = pos.cotacao_fonte if pos else None
    cotacao_usd_brl_preservada = pos.cotacao_usd_brl if pos else None
    preco_medio_manual_preservado = pos.preco_medio_manual if pos else None
    preco_medio_eh_manual_preservado = pos.preco_medio_eh_manual if pos else 0
    preco_teto_preservado = pos.preco_teto if pos else None

    if not pos:
        pos = PosicaoAtualAtivo(ativo_id=ativo_id)
        db.add(pos)

    pos.quantidade = qtd_liquida
    pos.quantidade_comprada_total = qtd_comprada
    pos.quantidade_vendida_total = qtd_vendida
    pos.custo_total = round(custo_total, 4)
    pos.preco_medio = round(preco_medio_calc, 8)
    pos.preco_medio_manual = preco_medio_manual_preservado
    pos.preco_medio_eh_manual = preco_medio_eh_manual_preservado
    pos.cotacao_atual = cotacao_atual_preservada
    pos.cotacao_atual_data = cotacao_data_preservada
    pos.cotacao_fonte = cotacao_fonte_preservada
    pos.cotacao_usd_brl = cotacao_usd_brl_preservada
    pos.preco_teto = preco_teto_preservado
    pos.valor_atual_brl = _calcular_valor_brl(ativo, pos)

    if commit:
        db.commit()
        db.refresh(pos)
    else:
        db.flush()
    return pos


def _calcular_valor_brl(ativo: Ativo, pos: PosicaoAtualAtivo) -> float:
    if not pos.cotacao_atual or pos.quantidade <= 0:
        return 0.0
    valor_nativo = float(pos.quantidade) * float(pos.cotacao_atual)
    if ativo.moeda == "USD" and pos.cotacao_usd_brl:
        return round(valor_nativo * float(pos.cotacao_usd_brl), 2)
    return round(valor_nativo, 2)


def recalcular_todas_posicoes(db: Session) -> dict:
    ativos_ids = db.scalars(select(Ativo.id).where(Ativo.ativo == 1)).all()
    processados = 0
    for aid in ativos_ids:
        try:
            recalcular_posicao_ativo(db, aid, commit=False)
            processados += 1
        except Exception:
            pass
    db.commit()
    total_aportes = db.scalars(select(AporteBolsa.id)).all()
    return {
        "ativos_processados": processados,
        "aportes_processados": len(total_aportes),
        "mensagem": f"Recalculadas posições de {processados} ativos com base em {len(total_aportes)} aportes.",
    }


def definir_preco_medio_manual(db: Session, ativo_id: int, preco: float) -> PosicaoAtualAtivo:
    ativo = db.get(Ativo, ativo_id)
    if not ativo:
        raise ValueError("Ativo não encontrado")
    pos = db.scalar(select(PosicaoAtualAtivo).where(PosicaoAtualAtivo.ativo_id == ativo_id))
    if not pos:
        pos = recalcular_posicao_ativo(db, ativo_id, commit=False)
    pos.preco_medio_manual = preco
    pos.preco_medio_eh_manual = 1
    pos.valor_atual_brl = _calcular_valor_brl(ativo, pos)
    db.commit()
    db.refresh(pos)
    return pos


def voltar_preco_medio_automatico(db: Session, ativo_id: int) -> PosicaoAtualAtivo:
    ativo = db.get(Ativo, ativo_id)
    if not ativo:
        raise ValueError("Ativo não encontrado")
    pos = db.scalar(select(PosicaoAtualAtivo).where(PosicaoAtualAtivo.ativo_id == ativo_id))
    if not pos:
        raise ValueError("Posição não encontrada")
    pos.preco_medio_manual = None
    pos.preco_medio_eh_manual = 0
    pos.valor_atual_brl = _calcular_valor_brl(ativo, pos)
    db.commit()
    db.refresh(pos)
    return pos


def definir_preco_teto(db: Session, ativo_id: int, preco_teto: float) -> PosicaoAtualAtivo:
    """Define preço teto manual."""
    ativo = db.get(Ativo, ativo_id)
    if not ativo:
        raise ValueError("Ativo não encontrado")
    pos = db.scalar(select(PosicaoAtualAtivo).where(PosicaoAtualAtivo.ativo_id == ativo_id))
    if not pos:
        pos = recalcular_posicao_ativo(db, ativo_id, commit=False)
    pos.preco_teto = preco_teto
    db.commit()
    db.refresh(pos)
    return pos


def remover_preco_teto(db: Session, ativo_id: int) -> PosicaoAtualAtivo:
    """Remove preço teto."""
    ativo = db.get(Ativo, ativo_id)
    if not ativo:
        raise ValueError("Ativo não encontrado")
    pos = db.scalar(select(PosicaoAtualAtivo).where(PosicaoAtualAtivo.ativo_id == ativo_id))
    if not pos:
        raise ValueError("Posição não encontrada")
    pos.preco_teto = None
    db.commit()
    db.refresh(pos)
    return pos