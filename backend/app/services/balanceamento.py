"""
Service de balanceamento da carteira de renda variável.
Usa a POSIÇÃO ATUAL (visão única, sempre atualizada) como fonte da verdade.
- NÃO depende de ano/mês
- Reflete automaticamente os aportes lançados
"""
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.infrastructure.db.models import (
    Ativo, PosicaoAtualAtivo,
    BalanceamentoGeografia, BalanceamentoClasse, BalanceamentoAtivo
)
from app.services.conversao_bcb import obter_ou_buscar_cotacao
from app.infrastructure.db.models import Ano


TOLERANCIA_PCT = 1.0


def _calcular_status(atual: float, alvo: float | None) -> str:
    if alvo is None:
        return "sem_meta"
    diff = alvo - atual
    if abs(diff) <= TOLERANCIA_PCT:
        return "equilibrado"
    if diff > 0:
        return "abaixo"
    return "acima"


def _calcular_aporte_sugerido(
    total_carteira: float, atual_pct: float, alvo_pct: float | None
) -> float | None:
    if alvo_pct is None:
        return None
    gap_pct = alvo_pct - atual_pct
    if gap_pct <= TOLERANCIA_PCT:
        return None
    return round(total_carteira * gap_pct / 100, 2)


def analisar_balanceamento(db: Session) -> dict:
    """
    Analisa balanceamento da carteira de renda variável.
    Fonte: PosicaoAtualAtivo (sempre atualizada via aportes + cotações).
    """
    # ============================================================
    # 1. Carregar TODAS as posições atuais com quantidade > 0
    # ============================================================
    rows = db.execute(
        select(PosicaoAtualAtivo, Ativo)
        .join(Ativo, Ativo.id == PosicaoAtualAtivo.ativo_id)
        .where(PosicaoAtualAtivo.quantidade > 0)
    ).all()

    posicoes = []
    sem_cotacao = []
    for pos, ativo in rows:
        valor_brl = float(pos.valor_atual_brl)
        if valor_brl <= 0:
            sem_cotacao.append({
                "ticker": ativo.ticker,
                "motivo": "Sem cotação atual cadastrada"
            })
            continue
        posicoes.append({
            "ativo": ativo,
            "valor_brl": valor_brl,
            "cotacao_data": pos.cotacao_atual_data,
        })

    total_rv = sum(p["valor_brl"] for p in posicoes)

    # ============================================================
    # 2. Carregar metas
    # ============================================================
    config_geo = {
        c.geografia: float(c.percentual_alvo)
        for c in db.scalars(
            select(BalanceamentoGeografia).where(BalanceamentoGeografia.ativo == 1)
        ).all()
    }

    config_classe = {}
    for c in db.scalars(
        select(BalanceamentoClasse).where(BalanceamentoClasse.ativo == 1)
    ).all():
        config_classe[(c.geografia, c.classe)] = float(c.percentual_alvo)

    config_ativo = {}
    for c in db.scalars(
        select(BalanceamentoAtivo).where(BalanceamentoAtivo.ativo == 1)
    ).all():
        config_ativo[c.ativo_id] = float(c.percentual_alvo_carteira)

    # ============================================================
    # 3. Agregar por geografia
    # ============================================================
    agreg_geo: dict[str, float] = {}
    for p in posicoes:
        g = p["ativo"].geografia
        agreg_geo[g] = agreg_geo.get(g, 0) + p["valor_brl"]

    for g in config_geo:
        if g not in agreg_geo:
            agreg_geo[g] = 0

    por_geografia = []
    for g, valor in sorted(agreg_geo.items(), key=lambda x: -x[1]):
        atual_pct = (valor / total_rv * 100) if total_rv > 0 else 0
        alvo_pct = config_geo.get(g)
        aporte = _calcular_aporte_sugerido(total_rv, atual_pct, alvo_pct)
        por_geografia.append({
            "geografia": g,
            "valor_alocado_brl": round(valor, 2),
            "percentual_atual": round(atual_pct, 2),
            "percentual_alvo": alvo_pct,
            "gap_pct": round(alvo_pct - atual_pct, 2) if alvo_pct is not None else None,
            "aporte_sugerido_brl": aporte,
            "status": _calcular_status(atual_pct, alvo_pct),
        })

    # ============================================================
    # 4. Agregar por classe
    # ============================================================
    agreg_classe: dict[tuple[str, str], float] = {}
    for p in posicoes:
        key = (p["ativo"].geografia, p["ativo"].classe)
        agreg_classe[key] = agreg_classe.get(key, 0) + p["valor_brl"]

    for key in config_classe:
        if key not in agreg_classe:
            agreg_classe[key] = 0

    por_classe = []
    for (g, c), valor in sorted(agreg_classe.items(), key=lambda x: -x[1]):
        atual_pct = (valor / total_rv * 100) if total_rv > 0 else 0
        alvo_pct = config_classe.get((g, c))
        aporte = _calcular_aporte_sugerido(total_rv, atual_pct, alvo_pct)
        por_classe.append({
            "geografia": g,
            "classe": c,
            "valor_alocado_brl": round(valor, 2),
            "percentual_atual": round(atual_pct, 2),
            "percentual_alvo": alvo_pct,
            "gap_pct": round(alvo_pct - atual_pct, 2) if alvo_pct is not None else None,
            "aporte_sugerido_brl": aporte,
            "status": _calcular_status(atual_pct, alvo_pct),
        })

    # ============================================================
    # 5. Agregar por ativo
    # ============================================================
    agreg_ativo: dict[int, dict] = {}
    for p in posicoes:
        a = p["ativo"]
        if a.id not in agreg_ativo:
            agreg_ativo[a.id] = {
                "ativo": a, "valor_brl": 0,
                "cotacao_data": p["cotacao_data"],
            }
        agreg_ativo[a.id]["valor_brl"] += p["valor_brl"]

    for ativo_id_meta in config_ativo:
        if ativo_id_meta not in agreg_ativo:
            ativo_obj = db.get(Ativo, ativo_id_meta)
            if ativo_obj:
                agreg_ativo[ativo_id_meta] = {
                    "ativo": ativo_obj, "valor_brl": 0, "cotacao_data": None
                }

    por_ativo = []
    for ativo_id, info in agreg_ativo.items():
        if ativo_id not in config_ativo and info["valor_brl"] == 0:
            continue
        a = info["ativo"]
        valor = info["valor_brl"]
        atual_pct = (valor / total_rv * 100) if total_rv > 0 else 0
        alvo_pct = config_ativo.get(ativo_id)
        aporte = _calcular_aporte_sugerido(total_rv, atual_pct, alvo_pct)
        por_ativo.append({
            "ativo_id": ativo_id,
            "ticker": a.ticker,
            "nome": a.nome,
            "classe": a.classe,
            "geografia": a.geografia,
            "valor_alocado_brl": round(valor, 2),
            "percentual_atual": round(atual_pct, 2),
            "percentual_alvo": alvo_pct,
            "gap_pct": round(alvo_pct - atual_pct, 2) if alvo_pct is not None else None,
            "aporte_sugerido_brl": aporte,
            "status": _calcular_status(atual_pct, alvo_pct),
            "ultima_cotacao_em": info.get("cotacao_data"),
        })

    status_ordem = {"abaixo": 0, "acima": 1, "equilibrado": 2, "sem_meta": 3}
    por_ativo.sort(key=lambda x: (status_ordem[x["status"]], -x["valor_alocado_brl"]))

    # ============================================================
    # 6. Resumos de validação
    # ============================================================
    soma_geo = sum(config_geo.values())

    soma_classe_por_geo: dict[str, float] = {}
    for (g, c), pct in config_classe.items():
        soma_classe_por_geo[g] = soma_classe_por_geo.get(g, 0) + pct

    # Cotação USD/BRL corrente
    agora = datetime.utcnow()
    ano_obj = db.scalar(select(Ano).where(Ano.ano == agora.year))
    cotacao_usd_brl = None
    if ano_obj:
        cotacao_usd_brl = obter_ou_buscar_cotacao(db, ano_obj.id, agora.month)

    return {
        "calculado_em": agora,
        "total_rv_brl": round(total_rv, 2),
        "cotacao_usd_brl": cotacao_usd_brl,
        "qtd_ativos_com_posicao": len(posicoes),
        "qtd_ativos_sem_cotacao": len(sem_cotacao),
        "ativos_sem_cotacao": sem_cotacao,
        "por_geografia": por_geografia,
        "por_classe": por_classe,
        "por_ativo": por_ativo,
        "soma_alvos_geografia": round(soma_geo, 2),
        "soma_alvos_classe_por_geo": {
            k: round(v, 2) for k, v in soma_classe_por_geo.items()
        },
    }