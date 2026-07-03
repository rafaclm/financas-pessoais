"""
Service de consolidação patrimonial.
- M21: Consolidação de Renda Variável (BR + EUA + Cripto)
- M22: Consolidação Patrimonial Total
"""
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.infrastructure.db.models import (
    Ano, SaldoConta, SaldoInvestimento, ProdutoInvestimento,
    PosicaoCripto, PosicaoAtivoBR, PosicaoAtivoEUA, Ativo, Conta
)
from app.services.conversao_bcb import obter_ou_buscar_cotacao


# Cores semânticas para componentes (alinhadas ao padrão visual da Seção 12)
CORES_COMPONENTES = {
    "contas": "#3B82F6",
    "renda_fixa": "#06B6D4",
    "previdencia": "#8B5CF6",
    "fgts": "#A78BFA",
    "fundo": "#7C3AED",
    "outro": "#6366F1",
    "acoes_br": "#10B981",
    "etf_br": "#22C55E",
    "fii": "#84CC16",
    "fiagro": "#EAB308",
    "acoes_eua": "#F97316",
    "etf_eua": "#FB923C",
    "reit": "#EC4899",
    "cripto": "#F59E0B",
}

LABELS_COMPONENTES = {
    "contas": "Contas Correntes",
    "renda_fixa": "Renda Fixa",
    "previdencia": "Previdência",
    "fgts": "FGTS",
    "fundo": "Fundos",
    "outro": "Outros Investimentos",
    "acoes_br": "Ações BR",
    "etf_br": "ETF BR",
    "fii": "FIIs",
    "fiagro": "Fiagro",
    "acoes_eua": "Ações EUA",
    "etf_eua": "ETF EUA",
    "reit": "REITs",
    "cripto": "Criptoativos",
}


def _mes_anterior(db: Session, ano_id: int, mes: int) -> tuple[int | None, int | None]:
    if mes > 1:
        return ano_id, mes - 1
    ano_obj = db.get(Ano, ano_id)
    if not ano_obj:
        return None, None
    ano_ant = db.scalar(select(Ano).where(Ano.ano == ano_obj.ano - 1))
    return (ano_ant.id, 12) if ano_ant else (None, None)


def _mesmo_mes_ano_anterior(db: Session, ano_id: int, mes: int) -> tuple[int | None, int | None]:
    ano_obj = db.get(Ano, ano_id)
    if not ano_obj:
        return None, None
    ano_ant = db.scalar(select(Ano).where(Ano.ano == ano_obj.ano - 1))
    return (ano_ant.id, mes) if ano_ant else (None, None)


# ============================================================
#  M21 — CONSOLIDAÇÃO DE RENDA VARIÁVEL
# ============================================================
def consolidar_renda_variavel(db: Session, ano_id: int, mes: int) -> dict:
    ano_obj = db.get(Ano, ano_id)
    if not ano_obj:
        raise ValueError("Ano inválido")

    # Ativos BR
    rows_br = db.execute(
        select(
            PosicaoAtivoBR.ativo_id,
            Ativo.ticker, Ativo.nome, Ativo.classe, Ativo.geografia,
            PosicaoAtivoBR.valor_total.label("valor_brl"),
        )
        .join(Ativo, Ativo.id == PosicaoAtivoBR.ativo_id)
        .where(PosicaoAtivoBR.ano_id == ano_id, PosicaoAtivoBR.mes == mes)
    ).all()
    total_br = sum(float(r.valor_brl) for r in rows_br)

    # Ativos EUA
    rows_eua = db.execute(
        select(
            PosicaoAtivoEUA.ativo_id,
            Ativo.ticker, Ativo.nome, Ativo.classe, Ativo.geografia,
            PosicaoAtivoEUA.valor_total_brl.label("valor_brl"),
        )
        .join(Ativo, Ativo.id == PosicaoAtivoEUA.ativo_id)
        .where(PosicaoAtivoEUA.ano_id == ano_id, PosicaoAtivoEUA.mes == mes)
    ).all()
    total_eua = sum(float(r.valor_brl) for r in rows_eua)

    # Cripto
    rows_cripto = db.execute(
        select(
            PosicaoCripto.ativo_id,
            Ativo.ticker, Ativo.nome, Ativo.classe, Ativo.geografia,
            PosicaoCripto.saldo_brl.label("valor_brl"),
        )
        .join(Ativo, Ativo.id == PosicaoCripto.ativo_id)
        .where(PosicaoCripto.ano_id == ano_id, PosicaoCripto.mes == mes)
    ).all()
    total_cripto = sum(float(r.valor_brl) for r in rows_cripto)

    total_geral = total_br + total_eua + total_cripto

    # ---------- Por Geografia ----------
    por_geografia_map: dict[str, dict] = {}
    for r in rows_br + rows_eua + rows_cripto:
        g = r.geografia
        if g not in por_geografia_map:
            por_geografia_map[g] = {"valor": 0.0, "qtd": 0}
        por_geografia_map[g]["valor"] += float(r.valor_brl)
        por_geografia_map[g]["qtd"] += 1

    por_geografia = [
        {
            "geografia": g,
            "valor_brl": v["valor"],
            "percentual_carteira": round(v["valor"] / total_geral * 100, 2) if total_geral else 0,
            "qtd_ativos": v["qtd"],
        }
        for g, v in sorted(por_geografia_map.items(), key=lambda x: -x[1]["valor"])
    ]

    # ---------- Por Classe ----------
    por_classe_map: dict[str, dict] = {}
    for r in rows_br + rows_eua + rows_cripto:
        c = r.classe
        if c not in por_classe_map:
            por_classe_map[c] = {"valor": 0.0, "qtd": 0}
        por_classe_map[c]["valor"] += float(r.valor_brl)
        por_classe_map[c]["qtd"] += 1

    por_classe = [
        {
            "classe": c,
            "valor_brl": v["valor"],
            "percentual_carteira": round(v["valor"] / total_geral * 100, 2) if total_geral else 0,
            "qtd_ativos": v["qtd"],
        }
        for c, v in sorted(por_classe_map.items(), key=lambda x: -x[1]["valor"])
    ]

    # ---------- Por Ativo ----------
    por_ativo = []
    for r in rows_br + rows_eua + rows_cripto:
        valor = float(r.valor_brl)
        por_ativo.append({
            "ativo_id": r.ativo_id,
            "ticker": r.ticker,
            "nome": r.nome,
            "classe": r.classe,
            "geografia": r.geografia,
            "valor_brl": valor,
            "percentual_carteira": round(valor / total_geral * 100, 2) if total_geral else 0,
        })
    por_ativo.sort(key=lambda x: -x["valor_brl"])

    return {
        "periodo": {"ano_id": ano_id, "ano": ano_obj.ano, "mes": mes},
        "total_brl": total_geral,
        "total_br_brl": total_br,
        "total_eua_brl": total_eua,
        "total_cripto_brl": total_cripto,
        "por_geografia": por_geografia,
        "por_classe": por_classe,
        "por_ativo": por_ativo,
    }


# ============================================================
#  M22 — CONSOLIDAÇÃO PATRIMONIAL TOTAL
# ============================================================
def _calcular_patrimonio(db: Session, ano_id: int, mes: int) -> dict:
    """Calcula totais do patrimônio para um período (sem variações)."""

    # ---------- LIQUIDEZ (contas correntes) ----------
    total_contas = float(db.scalar(
        select(func.coalesce(func.sum(SaldoConta.saldo_brl), 0))
        .where(SaldoConta.ano_id == ano_id, SaldoConta.mes == mes)
    ) or 0)

    # Para distribuição BRL/USD: separa moeda
    total_contas_brl = float(db.scalar(
        select(func.coalesce(func.sum(SaldoConta.saldo_brl), 0))
        .join(Conta, Conta.id == SaldoConta.conta_id)
        .where(SaldoConta.ano_id == ano_id, SaldoConta.mes == mes,
               Conta.moeda == "BRL")
    ) or 0)
    total_contas_usd = total_contas - total_contas_brl

    # ---------- RENDA FIXA por categoria ----------
    rows_rf = db.execute(
        select(
            ProdutoInvestimento.categoria,
            func.coalesce(func.sum(SaldoInvestimento.saldo_brl), 0).label("total"),
        )
        .join(ProdutoInvestimento, ProdutoInvestimento.id == SaldoInvestimento.produto_id)
        .where(SaldoInvestimento.ano_id == ano_id, SaldoInvestimento.mes == mes)
        .group_by(ProdutoInvestimento.categoria)
    ).all()

    investimentos_por_categoria: dict[str, float] = {}
    for r in rows_rf:
        investimentos_por_categoria[r.categoria] = float(r.total or 0)
    total_rf_geral = sum(investimentos_por_categoria.values())

    # ---------- RENDA VARIÁVEL por classe ----------
    # BR
    rows_rv_br = db.execute(
        select(
            Ativo.classe,
            func.coalesce(func.sum(PosicaoAtivoBR.valor_total), 0).label("total"),
        )
        .join(Ativo, Ativo.id == PosicaoAtivoBR.ativo_id)
        .where(PosicaoAtivoBR.ano_id == ano_id, PosicaoAtivoBR.mes == mes)
        .group_by(Ativo.classe)
    ).all()

    # EUA
    rows_rv_eua = db.execute(
        select(
            Ativo.classe,
            func.coalesce(func.sum(PosicaoAtivoEUA.valor_total_brl), 0).label("total"),
        )
        .join(Ativo, Ativo.id == PosicaoAtivoEUA.ativo_id)
        .where(PosicaoAtivoEUA.ano_id == ano_id, PosicaoAtivoEUA.mes == mes)
        .group_by(Ativo.classe)
    ).all()

    rv_br_por_classe: dict[str, float] = {}
    for r in rows_rv_br:
        rv_br_por_classe[r.classe] = float(r.total or 0)
    rv_eua_por_classe: dict[str, float] = {}
    for r in rows_rv_eua:
        rv_eua_por_classe[r.classe] = float(r.total or 0)

    total_rv_br = sum(rv_br_por_classe.values())
    total_rv_eua = sum(rv_eua_por_classe.values())
    total_rv = total_rv_br + total_rv_eua

    # ---------- CRIPTOATIVOS ----------
    total_cripto = float(db.scalar(
        select(func.coalesce(func.sum(PosicaoCripto.saldo_brl), 0))
        .where(PosicaoCripto.ano_id == ano_id, PosicaoCripto.mes == mes)
    ) or 0)

    # ---------- PATRIMÔNIO TOTAL ----------
    patrimonio_total = total_contas + total_rf_geral + total_rv + total_cripto

    # ---------- USD vs BRL ----------
    # USD: ativos EUA + contas USD + criptos (consideradas USD-pegged)
    total_usd_equiv = total_rv_eua + total_contas_usd + total_cripto
    total_brl_puro = patrimonio_total - total_usd_equiv

    # ---------- Componentes detalhados ----------
    componentes: list[dict] = []

    if total_contas > 0:
        componentes.append({
            "categoria": "contas",
            "label": LABELS_COMPONENTES["contas"],
            "valor_brl": total_contas,
            "percentual_total": round(total_contas / patrimonio_total * 100, 2) if patrimonio_total else 0,
            "cor": CORES_COMPONENTES["contas"],
        })

    for cat, valor in investimentos_por_categoria.items():
        if valor > 0:
            componentes.append({
                "categoria": cat,
                "label": LABELS_COMPONENTES.get(cat, cat.title()),
                "valor_brl": valor,
                "percentual_total": round(valor / patrimonio_total * 100, 2) if patrimonio_total else 0,
                "cor": CORES_COMPONENTES.get(cat, "#888888"),
            })

    # RV BR por classe
    for classe, valor in rv_br_por_classe.items():
        if valor > 0:
            key = f"{classe}_br" if classe in ("acao", "etf") else classe
            label_key = {
                "acao": "acoes_br", "etf": "etf_br", "fii": "fii", "fiagro": "fiagro"
            }.get(classe, classe)
            componentes.append({
                "categoria": label_key,
                "label": LABELS_COMPONENTES.get(label_key, classe.title() + " BR"),
                "valor_brl": valor,
                "percentual_total": round(valor / patrimonio_total * 100, 2) if patrimonio_total else 0,
                "cor": CORES_COMPONENTES.get(label_key, "#10B981"),
            })

    # RV EUA por classe
    for classe, valor in rv_eua_por_classe.items():
        if valor > 0:
            label_key = {
                "acao": "acoes_eua", "etf": "etf_eua", "reit": "reit"
            }.get(classe, classe)
            componentes.append({
                "categoria": label_key,
                "label": LABELS_COMPONENTES.get(label_key, classe.title() + " EUA"),
                "valor_brl": valor,
                "percentual_total": round(valor / patrimonio_total * 100, 2) if patrimonio_total else 0,
                "cor": CORES_COMPONENTES.get(label_key, "#F97316"),
            })

    # Cripto
    if total_cripto > 0:
        componentes.append({
            "categoria": "cripto",
            "label": LABELS_COMPONENTES["cripto"],
            "valor_brl": total_cripto,
            "percentual_total": round(total_cripto / patrimonio_total * 100, 2) if patrimonio_total else 0,
            "cor": CORES_COMPONENTES["cripto"],
        })

    # Ordena por valor desc
    componentes.sort(key=lambda x: -x["valor_brl"])

    return {
        "patrimonio_total": patrimonio_total,
        "total_liquidez": total_contas,
        "total_renda_fixa": total_rf_geral,
        "total_renda_variavel": total_rv,
        "total_cripto": total_cripto,
        "componentes": componentes,
        "pct_liquidez": round(total_contas / patrimonio_total * 100, 2) if patrimonio_total else 0,
        "pct_renda_fixa": round(total_rf_geral / patrimonio_total * 100, 2) if patrimonio_total else 0,
        "pct_renda_variavel": round(total_rv / patrimonio_total * 100, 2) if patrimonio_total else 0,
        "pct_cripto": round(total_cripto / patrimonio_total * 100, 2) if patrimonio_total else 0,
        "pct_brl": round(total_brl_puro / patrimonio_total * 100, 2) if patrimonio_total else 0,
        "pct_usd": round(total_usd_equiv / patrimonio_total * 100, 2) if patrimonio_total else 0,
    }


def _calcular_variacao(atual: float, referencia: float) -> dict | None:
    if referencia == 0:
        if atual == 0:
            return None
        return {
            "valor_atual": atual,
            "valor_referencia": 0,
            "diferenca": atual,
            "variacao_pct": 100.0,
        }
    return {
        "valor_atual": atual,
        "valor_referencia": referencia,
        "diferenca": atual - referencia,
        "variacao_pct": round((atual - referencia) / abs(referencia) * 100, 2),
    }


def consolidar_patrimonial(db: Session, ano_id: int, mes: int) -> dict:
    ano_obj = db.get(Ano, ano_id)
    if not ano_obj:
        raise ValueError("Ano inválido")

    atual = _calcular_patrimonio(db, ano_id, mes)

    # Comparativo mês anterior
    var_mes_ant = None
    ano_id_ant, mes_ant = _mes_anterior(db, ano_id, mes)
    if ano_id_ant:
        anterior = _calcular_patrimonio(db, ano_id_ant, mes_ant)
        if anterior["patrimonio_total"] > 0:
            var_mes_ant = _calcular_variacao(
                atual["patrimonio_total"], anterior["patrimonio_total"]
            )

    # Comparativo mesmo mês ano anterior
    var_ano_ant = None
    ano_id_ano_ant, mes_ano_ant = _mesmo_mes_ano_anterior(db, ano_id, mes)
    if ano_id_ano_ant:
        ano_ant = _calcular_patrimonio(db, ano_id_ano_ant, mes_ano_ant)
        if ano_ant["patrimonio_total"] > 0:
            var_ano_ant = _calcular_variacao(
                atual["patrimonio_total"], ano_ant["patrimonio_total"]
            )

    cotacao = obter_ou_buscar_cotacao(db, ano_id, mes)

    return {
        "periodo": {"ano_id": ano_id, "ano": ano_obj.ano, "mes": mes},
        **atual,
        "variacao_mes_anterior": var_mes_ant,
        "variacao_ano_anterior": var_ano_ant,
        "cotacao_usd_brl": cotacao,
    }