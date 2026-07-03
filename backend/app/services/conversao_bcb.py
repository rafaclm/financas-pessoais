"""
Service de integracao com a API do Banco Central do Brasil (PTAX).
Busca cotacoes USD/BRL historicas.
"""
import calendar
from datetime import date, datetime
from typing import Optional
import httpx
from loguru import logger
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.infrastructure.db.models import CotacaoCambio, Ano


BCB_URL_TEMPLATE = (
    "https://api.bcb.gov.br/dados/serie/bcdata.sgs.1/dados"
    "?formato=json&dataInicial={inicio}&dataFinal={fim}"
)


def _ultimo_dia_mes(ano: int, mes: int) -> int:
    return calendar.monthrange(ano, mes)[1]


def buscar_cotacao_bcb(ano: int, mes: int) -> Optional[float]:
    """Busca a ultima cotacao do mes na API do BCB."""
    dia_inicio = f"01/{mes:02d}/{ano}"
    dia_fim = f"{_ultimo_dia_mes(ano, mes):02d}/{mes:02d}/{ano}"
    url = BCB_URL_TEMPLATE.format(inicio=dia_inicio, fim=dia_fim)

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(url)
            resp.raise_for_status()
            dados = resp.json()
            if not dados:
                logger.warning(f"BCB sem dados para {mes:02d}/{ano}")
                return None
            ultima = dados[-1]
            valor = float(ultima.get("valor", 0))
            logger.info(f"BCB cotacao {mes:02d}/{ano}: {valor}")
            return valor if valor > 0 else None
    except Exception as e:
        logger.warning(f"Falha BCB: {e}")
        return None


def buscar_cotacao_bcb_por_data(data_alvo: date) -> Optional[float]:
    """
    🆕 Busca a cotacao USD/BRL para uma data especifica.
    Estrategia: busca um range de 7 dias antes da data alvo e retorna
    a cotacao mais proxima/anterior.
    """
    from datetime import timedelta

    # Range de 7 dias antes ate a data alvo
    data_inicio = data_alvo - timedelta(days=7)
    data_fim = data_alvo
    inicio_str = data_inicio.strftime("%d/%m/%Y")
    fim_str = data_fim.strftime("%d/%m/%Y")
    url = BCB_URL_TEMPLATE.format(inicio=inicio_str, fim=fim_str)

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(url)
            resp.raise_for_status()
            dados = resp.json()
            if not dados:
                logger.warning(f"BCB sem dados para data {data_alvo}")
                return None
            # Pega a ultima cotacao do periodo (mais proxima da data alvo)
            ultima = dados[-1]
            valor = float(ultima.get("valor", 0))
            return valor if valor > 0 else None
    except Exception as e:
        logger.warning(f"Falha BCB por data {data_alvo}: {e}")
        return None


def obter_cotacao_por_data(db: Session, data_alvo: date) -> Optional[float]:
    """
    🆕 Obtem cotacao USD/BRL para uma data especifica.
    1. Tenta buscar no BCB (data exata)
    2. Se falhar, usa cotacao do mes (mais aproximada)
    3. Se ainda falhar, usa fallback (cotacao mais recente disponivel no banco)
    """
    cotacao = buscar_cotacao_bcb_por_data(data_alvo)
    if cotacao:
        return cotacao

    # Fallback 1: cotacao do mes da data
    ano_obj = db.scalar(select(Ano).where(Ano.ano == data_alvo.year))
    if ano_obj:
        cotacao = obter_ou_buscar_cotacao(db, ano_obj.id, data_alvo.month)
        if cotacao:
            return cotacao

    # Fallback 2: cotacao mais recente do banco
    fallback = db.scalar(
        select(CotacaoCambio)
        .where(CotacaoCambio.par == "USDBRL")
        .order_by(CotacaoCambio.ano_id.desc(), CotacaoCambio.mes.desc())
        .limit(1)
    )
    if fallback:
        logger.warning(f"Usando cotacao fallback para data {data_alvo}")
        return float(fallback.cotacao)

    return None


def obter_ou_buscar_cotacao(
    db: Session,
    ano_id: int,
    mes: int,
    par: str = "USDBRL",
    forcar_atualizacao: bool = False,
) -> Optional[float]:
    """Mesma logica anterior (busca mensal)."""
    cot_existente = db.scalar(
        select(CotacaoCambio).where(
            CotacaoCambio.ano_id == ano_id,
            CotacaoCambio.mes == mes,
            CotacaoCambio.par == par,
        )
    )

    if cot_existente and not forcar_atualizacao:
        return float(cot_existente.cotacao)

    ano_obj = db.get(Ano, ano_id)
    if not ano_obj:
        return None
    ano_num = ano_obj.ano

    valor_bcb = buscar_cotacao_bcb(ano_num, mes)

    if valor_bcb:
        if cot_existente:
            cot_existente.cotacao = valor_bcb
            cot_existente.fonte = "bcb"
        else:
            cot_existente = CotacaoCambio(
                ano_id=ano_id, mes=mes, par=par,
                cotacao=valor_bcb, fonte="bcb"
            )
            db.add(cot_existente)
        db.commit()
        return valor_bcb

    fallback = db.scalar(
        select(CotacaoCambio)
        .where(CotacaoCambio.par == par)
        .order_by(CotacaoCambio.ano_id.desc(), CotacaoCambio.mes.desc())
        .limit(1)
    )
    if fallback:
        return float(fallback.cotacao)

    return None