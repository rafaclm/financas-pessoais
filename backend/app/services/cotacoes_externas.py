"""
Service de integracao com APIs externas de cotacoes.
- brapi.dev (acoes/FIIs/ETFs BR) - usa token se disponivel
- Yahoo Finance (acoes/ETFs/REITs EUA)
- CoinGecko (criptoativos)

Inclui:
- Logs detalhados de cada erro
- Retry com backoff em rate limits
- Mensagens de erro especificas para o frontend
"""
import time
import httpx
from datetime import datetime
from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.infrastructure.db.models import Ativo, PosicaoAtualAtivo
from app.services.posicao_atual import _calcular_valor_brl
from app.core.config import settings


CRIPTO_MAP_COINGECKO = {
    "BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana",
    "ADA": "cardano", "DOT": "polkadot", "MATIC": "matic-network",
    "LINK": "chainlink", "AVAX": "avalanche-2", "USDT": "tether",
    "USDC": "usd-coin", "BNB": "binancecoin", "XRP": "ripple",
    "DOGE": "dogecoin", "BAL": "balancer", "1INCH": "1inch",
}


# ============================================================
#  B3 — brapi.dev (com retry + token)
# ============================================================
def buscar_cotacao_b3(ticker: str, tentativas: int = 2) -> tuple[float | None, str | None]:
    """
    Busca cotacao via brapi.dev.
    Retorna (cotacao, mensagem_erro)
    """
    url = f"https://brapi.dev/api/quote/{ticker.upper()}"

    # Adiciona token se disponivel
    params = {}
    if settings.brapi_token:
        params["token"] = settings.brapi_token

    ultimo_erro = "Sem detalhes"

    for tentativa in range(tentativas):
        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.get(url, params=params)

                # Trata diferentes codigos de erro
                if resp.status_code == 401:
                    return None, "Token brapi.dev invalido ou expirado"
                if resp.status_code == 404:
                    return None, f"Ticker '{ticker}' nao encontrado na brapi.dev"
                if resp.status_code == 402:
                    return None, "brapi.dev: requer plano pago (cadastre token gratuito)"
                if resp.status_code == 429:
                    # Rate limit - tenta de novo apos 1 segundo
                    if tentativa < tentativas - 1:
                        logger.warning(f"Rate limit em {ticker}, aguardando 2s...")
                        time.sleep(2)
                        continue
                    return None, "Rate limit excedido (cadastre token gratuito em brapi.dev)"

                resp.raise_for_status()
                data = resp.json()

                results = data.get("results", [])
                if not results:
                    return None, f"brapi.dev sem resultados para {ticker}"

                result = results[0]
                preco = result.get("regularMarketPrice")
                if preco is None or preco == 0:
                    erro_msg = result.get("error", "preco nao retornado")
                    return None, f"brapi.dev: {erro_msg}"

                return float(preco), None

        except httpx.TimeoutException:
            ultimo_erro = "Timeout (15s)"
            if tentativa < tentativas - 1:
                time.sleep(1)
                continue
        except httpx.HTTPStatusError as e:
            ultimo_erro = f"HTTP {e.response.status_code}"
        except Exception as e:
            ultimo_erro = f"Erro inesperado: {type(e).__name__}: {e}"
            logger.error(f"brapi falha {ticker}: {ultimo_erro}")

    return None, ultimo_erro


# ============================================================
#  EUA — Yahoo Finance
# ============================================================
def buscar_cotacao_yahoo(ticker: str) -> tuple[float | None, str | None]:
    """Retorna (cotacao, erro)."""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker.upper()}"
    try:
        with httpx.Client(
            timeout=10.0,
            headers={"User-Agent": "Mozilla/5.0 (Finance App)"}
        ) as client:
            resp = client.get(url)
            if resp.status_code == 404:
                return None, f"Yahoo: ticker '{ticker}' nao encontrado"
            resp.raise_for_status()
            data = resp.json()
            result = data.get("chart", {}).get("result", [])
            if not result:
                return None, "Yahoo: sem resultados"
            meta = result[0].get("meta", {})
            preco = meta.get("regularMarketPrice")
            if preco is None:
                return None, "Yahoo: preco nao retornado"
            return float(preco), None
    except httpx.TimeoutException:
        return None, "Yahoo: timeout"
    except Exception as e:
        return None, f"Yahoo: {type(e).__name__}: {e}"


# ============================================================
#  CRIPTO — CoinGecko
# ============================================================
def buscar_cotacao_cripto(ticker: str) -> tuple[dict | None, str | None]:
    """Retorna ({'usd': X, 'brl': Y}, erro)."""
    coin_id = CRIPTO_MAP_COINGECKO.get(ticker.upper())
    if not coin_id:
        return None, f"Cripto '{ticker}' nao tem mapeamento no CoinGecko"

    url = (
        f"https://api.coingecko.com/api/v3/simple/price"
        f"?ids={coin_id}&vs_currencies=usd,brl"
    )
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(url)
            if resp.status_code == 429:
                return None, "CoinGecko: rate limit"
            resp.raise_for_status()
            data = resp.json()
            preco = data.get(coin_id)
            if not preco:
                return None, f"CoinGecko: '{coin_id}' sem dados"
            return {"usd": preco.get("usd"), "brl": preco.get("brl")}, None
    except httpx.TimeoutException:
        return None, "CoinGecko: timeout"
    except Exception as e:
        return None, f"CoinGecko: {type(e).__name__}: {e}"


# ============================================================
#  ORQUESTRACAO
# ============================================================
def atualizar_cotacao_via_api(
    db: Session, ativo: Ativo, cotacao_usd_brl: float | None = None
) -> dict:
    """Busca cotacao de UM ativo na API apropriada."""
    cotacao = None
    fonte = None
    erro = None

    try:
        if ativo.classe == "cripto":
            r, err = buscar_cotacao_cripto(ativo.ticker)
            if r:
                if r.get("brl"):
                    cotacao = r["brl"]
                    fonte = "coingecko_brl"
                elif r.get("usd"):
                    cotacao = r["usd"]
                    fonte = "coingecko_usd"
                else:
                    erro = "CoinGecko sem precos retornados"
            else:
                erro = err
        elif ativo.geografia == "BR":
            cotacao, err = buscar_cotacao_b3(ativo.ticker)
            fonte = "brapi"
            if not cotacao:
                erro = err
        elif ativo.geografia == "EUA":
            cotacao, err = buscar_cotacao_yahoo(ativo.ticker)
            fonte = "yahoo"
            if not cotacao:
                erro = err
        else:
            erro = f"Geografia '{ativo.geografia}' nao suportada"

    except Exception as e:
        erro = f"Excecao inesperada: {type(e).__name__}: {e}"

    if cotacao is None:
        return {"ok": False, "cotacao": None, "fonte": fonte, "erro": erro}

    pos = db.scalar(select(PosicaoAtualAtivo).where(PosicaoAtualAtivo.ativo_id == ativo.id))
    if not pos:
        return {"ok": True, "cotacao": cotacao, "fonte": fonte,
                "erro": "Sem posicao cadastrada"}

    pos.cotacao_atual = cotacao
    pos.cotacao_atual_data = datetime.utcnow()
    pos.cotacao_fonte = fonte

    if ativo.moeda == "USD" or (ativo.classe == "cripto" and fonte == "coingecko_usd"):
        if cotacao_usd_brl:
            pos.cotacao_usd_brl = cotacao_usd_brl

    pos.valor_atual_brl = _calcular_valor_brl(ativo, pos)
    db.flush()

    return {"ok": True, "cotacao": cotacao, "fonte": fonte, "erro": None}


def atualizar_todas_cotacoes(db: Session) -> dict:
    """Atualiza cotacoes de todos os ativos com posicao > 0."""
    from app.services.conversao_bcb import obter_ou_buscar_cotacao
    from datetime import datetime as dt
    from app.infrastructure.db.models import Ano

    hoje = dt.utcnow()
    ano_obj = db.scalar(select(Ano).where(Ano.ano == hoje.year))
    cotacao_usd_brl = None
    if ano_obj:
        cotacao_usd_brl = obter_ou_buscar_cotacao(db, ano_obj.id, hoje.month)

    posicoes = db.scalars(
        select(PosicaoAtualAtivo).where(PosicaoAtualAtivo.quantidade > 0)
    ).all()

    atualizados = 0
    falhas = 0
    detalhes = []

    for i, pos in enumerate(posicoes):
        ativo = db.get(Ativo, pos.ativo_id)
        if not ativo:
            falhas += 1
            continue

        # 🆕 Para nao atingir rate limit, pausa pequena entre BR
        if ativo.geografia == "BR" and not settings.brapi_token:
            if i > 0:
                time.sleep(0.5)  # 500ms entre chamadas BR sem token

        r = atualizar_cotacao_via_api(db, ativo, cotacao_usd_brl)
        if r["ok"] and r["cotacao"]:
            atualizados += 1
            detalhes.append({
                "ticker": ativo.ticker,
                "cotacao": r["cotacao"],
                "fonte": r["fonte"],
                "status": "ok"
            })
        else:
            falhas += 1
            detalhes.append({
                "ticker": ativo.ticker,
                "cotacao": None,
                "fonte": r.get("fonte"),
                "status": "erro",
                "erro": r.get("erro") or "Erro desconhecido",
            })
            # 🆕 Log detalhado de cada erro
            logger.warning(
                f"Cotacao {ativo.ticker} ({ativo.geografia}/{ativo.classe}): "
                f"{r.get('erro') or 'sem detalhe'}"
            )

    db.commit()

    # Mensagem mais informativa
    msg_extra = ""
    if falhas > atualizados and not settings.brapi_token:
        msg_extra = (
            " ⚠️ Dica: muitas falhas na brapi.dev — "
            "cadastre o token gratuito em brapi.dev (15.000 chamadas/dia)."
        )

    return {
        "atualizados": atualizados,
        "falhas": falhas,
        "total": len(posicoes),
        "mensagem": (
            f"{atualizados} cotacoes atualizadas, "
            f"{falhas} falhas de {len(posicoes)} ativos.{msg_extra}"
        ),
        "detalhes": detalhes,
    }