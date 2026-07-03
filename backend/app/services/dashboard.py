"""
Service que agrega dados para o Dashboard principal.
"""
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.infrastructure.db.models import (
    Ano, SaldoConta, SaldoInvestimento, ProdutoInvestimento,
    PosicaoAtualAtivo, Ativo, Conta,
    PosicaoCripto, PosicaoAtivoBR, PosicaoAtivoEUA,
    LancamentoReceita, LancamentoDespesa, Provento,
)
from app.services.consolidacao import _calcular_patrimonio


MESES_ABREV = [
    "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
    "Jul", "Ago", "Set", "Out", "Nov", "Dez"
]


def gerar_dados_dashboard(db: Session) -> dict:
    """Gera todos os dados do dashboard de uma vez."""
    hoje = datetime.utcnow()

    evolucao = _calcular_evolucao_patrimonial(db, hoje, meses=24)
    distribuicao = _calcular_distribuicao_carteira(db)
    receitas_despesas = _calcular_receitas_despesas(db, hoje, meses=12)
    renda_passiva = _calcular_renda_passiva(db, hoje, meses=24)
    kpis = _calcular_kpis(db, hoje, evolucao, renda_passiva)

    # 🆕 Novos cálculos
    comparativo_anual = _calcular_comparativo_anual(db)
    saldo_investimentos = _calcular_saldo_investimentos(db, hoje, meses=24)
    distribuicao_mensal = _calcular_distribuicao_mensal(db, hoje, meses=12)

    return {
        "timestamp": hoje,
        "kpis": kpis,
        "evolucao_patrimonial": evolucao,
        "distribuicao_carteira": distribuicao,
        "receitas_despesas": receitas_despesas,
        "renda_passiva": renda_passiva,
        "comparativo_anual": comparativo_anual,
        "saldo_investimentos": saldo_investimentos,
        "distribuicao_mensal": distribuicao_mensal,
    }


def _gerar_periodos(hoje: datetime, meses: int) -> list:
    """Gera lista de (ano, mes, label) dos ultimos N meses."""
    periodos = []
    ano = hoje.year
    mes = hoje.month
    for _ in range(meses):
        label = f"{MESES_ABREV[mes-1]}/{str(ano)[-2:]}"
        periodos.append((ano, mes, label))
        mes -= 1
        if mes == 0:
            mes = 12
            ano -= 1
    return list(reversed(periodos))


def _calcular_evolucao_patrimonial(db: Session, hoje: datetime, meses: int = 24) -> list:
    pontos = []
    periodos = _gerar_periodos(hoje, meses)
    for ano, mes, label in periodos:
        ano_obj = db.scalar(select(Ano).where(Ano.ano == ano))
        if not ano_obj:
            pontos.append({"ano": ano, "mes": mes, "label": label, "patrimonio_total": 0})
            continue
        try:
            patrimonio = _calcular_patrimonio(db, ano_obj.id, mes)
            pontos.append({
                "ano": ano, "mes": mes, "label": label,
                "patrimonio_total": round(patrimonio["patrimonio_total"], 2),
            })
        except Exception:
            pontos.append({"ano": ano, "mes": mes, "label": label, "patrimonio_total": 0})
    return pontos


def _calcular_distribuicao_carteira(db: Session) -> list:
    rv_br = 0
    rv_eua = 0
    cripto = 0
    rows = db.execute(
        select(PosicaoAtualAtivo, Ativo)
        .join(Ativo, Ativo.id == PosicaoAtualAtivo.ativo_id)
        .where(PosicaoAtualAtivo.quantidade > 0)
    ).all()
    for pos, ativo in rows:
        valor = float(pos.valor_atual_brl)
        if ativo.classe == "cripto":
            cripto += valor
        elif ativo.geografia == "BR":
            rv_br += valor
        elif ativo.geografia == "EUA":
            rv_eua += valor

    ultimo_saldo_conta = db.execute(
        select(SaldoConta.ano_id, SaldoConta.mes)
        .order_by(SaldoConta.ano_id.desc(), SaldoConta.mes.desc())
        .limit(1)
    ).first()
    liquidez = 0
    if ultimo_saldo_conta:
        liquidez_raw = db.scalar(
            select(func.coalesce(func.sum(SaldoConta.saldo_brl), 0))
            .where(
                SaldoConta.ano_id == ultimo_saldo_conta.ano_id,
                SaldoConta.mes == ultimo_saldo_conta.mes,
            )
        )
        liquidez = float(liquidez_raw or 0)

    ultimo_saldo_inv = db.execute(
        select(SaldoInvestimento.ano_id, SaldoInvestimento.mes)
        .order_by(SaldoInvestimento.ano_id.desc(), SaldoInvestimento.mes.desc())
        .limit(1)
    ).first()
    renda_fixa = 0
    if ultimo_saldo_inv:
        rf_raw = db.scalar(
            select(func.coalesce(func.sum(SaldoInvestimento.saldo_brl), 0))
            .where(
                SaldoInvestimento.ano_id == ultimo_saldo_inv.ano_id,
                SaldoInvestimento.mes == ultimo_saldo_inv.mes,
            )
        )
        renda_fixa = float(rf_raw or 0)

    fatias = []
    if liquidez > 0:
        fatias.append({"categoria": "💰 Liquidez", "valor": round(liquidez, 2), "cor": "#3B82F6"})
    if renda_fixa > 0:
        fatias.append({"categoria": "🏦 Renda Fixa", "valor": round(renda_fixa, 2), "cor": "#06B6D4"})
    if rv_br > 0:
        fatias.append({"categoria": "🇧🇷 RV Brasil", "valor": round(rv_br, 2), "cor": "#10B981"})
    if rv_eua > 0:
        fatias.append({"categoria": "🇺🇸 RV EUA", "valor": round(rv_eua, 2), "cor": "#F97316"})
    if cripto > 0:
        fatias.append({"categoria": "₿ Cripto", "valor": round(cripto, 2), "cor": "#F59E0B"})
    return fatias


def _calcular_receitas_despesas(db: Session, hoje: datetime, meses: int = 12) -> list:
    resultado = []
    periodos = _gerar_periodos(hoje, meses)
    for ano, mes, label in periodos:
        ano_obj = db.scalar(select(Ano).where(Ano.ano == ano))
        if not ano_obj:
            resultado.append({"label": label, "receitas": 0, "despesas": 0, "saldo": 0})
            continue
        rec = db.scalar(
            select(func.coalesce(func.sum(LancamentoReceita.valor), 0))
            .where(LancamentoReceita.ano_id == ano_obj.id, LancamentoReceita.mes == mes)
        ) or 0
        desp = db.scalar(
            select(func.coalesce(func.sum(LancamentoDespesa.valor), 0))
            .where(LancamentoDespesa.ano_id == ano_obj.id, LancamentoDespesa.mes == mes)
        ) or 0
        resultado.append({
            "label": label,
            "receitas": round(float(rec), 2),
            "despesas": round(float(desp), 2),
            "saldo": round(float(rec) - float(desp), 2),
        })
    return resultado


def _calcular_renda_passiva(db: Session, hoje: datetime, meses: int = 24) -> list:
    resultado = []
    periodos = _gerar_periodos(hoje, meses)
    for ano, mes, label in periodos:
        ano_obj = db.scalar(select(Ano).where(Ano.ano == ano))
        if not ano_obj:
            resultado.append({"label": label, "total": 0})
            continue
        total = db.scalar(
            select(func.coalesce(func.sum(Provento.valor_liquido_brl), 0))
            .where(Provento.ano_id == ano_obj.id, Provento.mes == mes)
        ) or 0
        resultado.append({"label": label, "total": round(float(total), 2)})
    return resultado


def _calcular_kpis(db: Session, hoje: datetime, evolucao: list, renda_passiva: list) -> dict:
    patrimonio_atual = evolucao[-1]["patrimonio_total"] if evolucao else 0
    patrimonio_mes_ant = evolucao[-2]["patrimonio_total"] if len(evolucao) > 1 else 0
    variacao_mes = None
    if patrimonio_mes_ant > 0:
        variacao_mes = round(
            (patrimonio_atual - patrimonio_mes_ant) / patrimonio_mes_ant * 100, 2
        )
    proventos_mes = renda_passiva[-1]["total"] if renda_passiva else 0

    rows = db.execute(
        select(PosicaoAtualAtivo, Ativo)
        .join(Ativo, Ativo.id == PosicaoAtualAtivo.ativo_id)
        .where(PosicaoAtualAtivo.quantidade > 0)
    ).all()
    valor_usd = 0
    valor_total = 0
    for pos, ativo in rows:
        v = float(pos.valor_atual_brl)
        valor_total += v
        if ativo.moeda == "USD":
            valor_usd += v

    rows_contas = db.execute(
        select(SaldoConta, Conta)
        .join(Conta, Conta.id == SaldoConta.conta_id)
        .order_by(SaldoConta.ano_id.desc(), SaldoConta.mes.desc())
    ).all()
    contas_processadas = set()
    for sc, conta in rows_contas:
        if conta.id in contas_processadas:
            continue
        contas_processadas.add(conta.id)
        v = float(sc.saldo_brl)
        valor_total += v
        if conta.moeda == "USD":
            valor_usd += v

    pct_usd = round(valor_usd / valor_total * 100, 2) if valor_total > 0 else 0
    pct_brl = 100 - pct_usd

    return {
        "patrimonio_total": patrimonio_atual,
        "variacao_mes_pct": variacao_mes,
        "proventos_mes": proventos_mes,
        "distribuicao_brl_pct": pct_brl,
        "distribuicao_usd_pct": pct_usd,
    }


# ============================================================
# 🆕 NOVOS CALCULOS
# ============================================================

def _calcular_comparativo_anual(db: Session) -> list:
    """Calcula totais consolidados por ano (2024, 2025, 2026)."""
    resultado = []
    anos = db.scalars(select(Ano).order_by(Ano.ano)).all()
    for ano in anos:
        receitas = db.scalar(
            select(func.coalesce(func.sum(LancamentoReceita.valor), 0))
            .where(LancamentoReceita.ano_id == ano.id)
        ) or 0
        despesas = db.scalar(
            select(func.coalesce(func.sum(LancamentoDespesa.valor), 0))
            .where(LancamentoDespesa.ano_id == ano.id)
        ) or 0
        proventos = db.scalar(
            select(func.coalesce(func.sum(Provento.valor_liquido_brl), 0))
            .where(Provento.ano_id == ano.id)
        ) or 0
        resultado.append({
            "ano": ano.ano,
            "receitas": round(float(receitas), 2),
            "despesas": round(float(despesas), 2),
            "saldo": round(float(receitas) - float(despesas), 2),
            "proventos": round(float(proventos), 2),
        })
    return resultado


def _calcular_saldo_investimentos(db: Session, hoje: datetime, meses: int = 24) -> list:
    """Calcula evolucao do saldo de investimentos por categoria."""
    resultado = []
    periodos = _gerar_periodos(hoje, meses)

    for ano, mes, label in periodos:
        ano_obj = db.scalar(select(Ano).where(Ano.ano == ano))
        ponto = {
            "label": label,
            "renda_fixa": 0, "previdencia": 0, "fgts": 0,
            "cripto": 0, "rv_br": 0, "rv_eua": 0,
        }
        if not ano_obj:
            resultado.append(ponto)
            continue

        # Saldos de Investimentos por categoria
        rows_inv = db.execute(
            select(ProdutoInvestimento.categoria, func.sum(SaldoInvestimento.saldo_brl))
            .join(ProdutoInvestimento, ProdutoInvestimento.id == SaldoInvestimento.produto_id)
            .where(SaldoInvestimento.ano_id == ano_obj.id, SaldoInvestimento.mes == mes)
            .group_by(ProdutoInvestimento.categoria)
        ).all()
        for cat, valor in rows_inv:
            v = float(valor or 0)
            if cat == "renda_fixa":
                ponto["renda_fixa"] = round(v, 2)
            elif cat == "previdencia":
                ponto["previdencia"] = round(v, 2)
            elif cat == "fgts":
                ponto["fgts"] = round(v, 2)

        # Cripto
        cripto_total = db.scalar(
            select(func.coalesce(func.sum(PosicaoCripto.saldo_brl), 0))
            .where(PosicaoCripto.ano_id == ano_obj.id, PosicaoCripto.mes == mes)
        ) or 0
        ponto["cripto"] = round(float(cripto_total), 2)

        # Ativos BR (do mes)
        br_total = db.scalar(
            select(func.coalesce(func.sum(PosicaoAtivoBR.valor_total), 0))
            .where(PosicaoAtivoBR.ano_id == ano_obj.id, PosicaoAtivoBR.mes == mes)
        ) or 0
        ponto["rv_br"] = round(float(br_total), 2)

        # Ativos EUA (do mes)
        eua_total = db.scalar(
            select(func.coalesce(func.sum(PosicaoAtivoEUA.valor_total_brl), 0))
            .where(PosicaoAtivoEUA.ano_id == ano_obj.id, PosicaoAtivoEUA.mes == mes)
        ) or 0
        ponto["rv_eua"] = round(float(eua_total), 2)

        resultado.append(ponto)

    return resultado


def _calcular_distribuicao_mensal(db: Session, hoje: datetime, meses: int = 12) -> list:
    """Calcula distribuicao BR/EUA/Cripto por mes (para grafico de area empilhada)."""
    saldos = _calcular_saldo_investimentos(db, hoje, meses)
    return [
        {
            "label": p["label"],
            "rv_br": p["rv_br"],
            "rv_eua": p["rv_eua"],
            "cripto": p["cripto"],
        }
        for p in saldos
    ]