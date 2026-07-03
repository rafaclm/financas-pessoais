"""
Importador de ativos a partir das abas:
- Cripto (BTC, ETH, BAL, 1INCH)
- Ativos BRA (acoes/FIIs BR)
- Ativos EUA (acoes/ETFs EUA)
"""
from sqlalchemy.orm import Session
from sqlalchemy import select
from openpyxl.workbook import Workbook
from loguru import logger
from app.infrastructure.db.models import Ativo
from app.services.importacao.leitor_excel import encontrar_aba, ler_aba_como_lista
from app.services.importacao.importacao_base import (
    ResultadoImportacao, normalizar_ticker
)


def importar_ativos(db: Session, wb: Workbook, dry_run: bool = False) -> ResultadoImportacao:
    """
    Importa ativos das 3 abas (Cripto, Ativos BRA, Ativos EUA).
    Se o ativo ja existe (mesmo ticker), nao recria.
    """
    resultado = ResultadoImportacao()
    ativos_detectados = []

    # ============================================================
    # 1. ABA CRIPTO
    # ============================================================
    aba_cripto = encontrar_aba(wb, "Cripto")
    if aba_cripto:
        linhas = ler_aba_como_lista(wb, aba_cripto, max_linhas=20)
        # Procura por linhas com Nome (col E=4) + Ticker (col F=5)
        for linha in linhas:
            if len(linha) >= 6:
                nome = linha[4]  # coluna E
                ticker = normalizar_ticker(linha[5])  # coluna F
                if nome and ticker and ticker != "TICKER":
                    ativos_detectados.append({
                        "ticker": ticker,
                        "nome": str(nome).strip(),
                        "tipo": "cripto",
                        "mercado": "CRIPTO",
                        "geografia": "GLOBAL",
                        "classe": "cripto",
                        "moeda": "BRL",  # gerenciamos em BRL
                        "setor": None,
                    })

    # ============================================================
    # 2. ABA ATIVOS BRA
    # ============================================================
    aba_br = encontrar_aba(wb, "Ativos BRA") or encontrar_aba(wb, "Ativos BR")
    if aba_br:
        linhas = ler_aba_como_lista(wb, aba_br, max_linhas=50)
        # Cabecalho na linha 10 (indice 9): Ativo | Ticker | Segmento | Cotas | ...
        for i, linha in enumerate(linhas):
            if i < 10:
                continue  # pula cabecalho
            if len(linha) < 4:
                continue
            ticker = normalizar_ticker(linha[1])  # coluna B
            if not ticker or ticker in ("TICKER", "TOTAL"):
                continue
            segmento = linha[2] if len(linha) > 2 else None  # coluna C
            # Determina classe pelo ticker
            classe = _classificar_br(ticker, segmento)
            tipo = _tipo_br(ticker, classe)
            ativos_detectados.append({
                "ticker": ticker,
                "nome": str(segmento).strip() if segmento else ticker,
                "tipo": tipo,
                "mercado": "B3",
                "geografia": "BR",
                "classe": classe,
                "moeda": "BRL",
                "setor": str(segmento).strip() if segmento else None,
            })

    # ============================================================
    # 3. ABA ATIVOS EUA
    # ============================================================
    aba_eua = encontrar_aba(wb, "Ativos EUA") or encontrar_aba(wb, "Ativos USA")
    if aba_eua:
        linhas = ler_aba_como_lista(wb, aba_eua, max_linhas=50)
        for i, linha in enumerate(linhas):
            if i < 10:
                continue
            if len(linha) < 4:
                continue
            ticker = normalizar_ticker(linha[1])
            if not ticker or ticker in ("TICKER", "TOTAL"):
                continue
            segmento = linha[2] if len(linha) > 2 else None
            classe = _classificar_eua(ticker, segmento)
            tipo = _tipo_eua(ticker, classe)
            ativos_detectados.append({
                "ticker": ticker,
                "nome": str(segmento).strip() if segmento else ticker,
                "tipo": tipo,
                "mercado": "NYSE",  # padrao; pode ser NASDAQ tambem
                "geografia": "EUA",
                "classe": classe,
                "moeda": "USD",
                "setor": str(segmento).strip() if segmento else None,
            })

    # ============================================================
    # 4. PERSISTIR
    # ============================================================
    for ativo_dados in ativos_detectados:
        ticker = ativo_dados["ticker"]
        existente = db.scalar(select(Ativo).where(Ativo.ticker == ticker))
        if existente:
            resultado.pulados += 1
            continue
        if not dry_run:
            try:
                novo = Ativo(**ativo_dados)
                db.add(novo)
                resultado.inseridos += 1
                resultado.detalhes_inseridos.append(ticker)
            except Exception as e:
                resultado.erros += 1
                resultado.detalhes_erros.append(f"{ticker}: {e}")
        else:
            resultado.inseridos += 1  # simulacao
            resultado.detalhes_inseridos.append(ticker)

    if not dry_run:
        db.commit()

    resultado.mensagem = (
        f"Ativos: {resultado.inseridos} novos, "
        f"{resultado.pulados} ja existiam, "
        f"{resultado.erros} erros."
    )
    logger.info(resultado.mensagem)
    return resultado


# ============================================================
# HELPERS de classificacao
# ============================================================
def _classificar_br(ticker: str, segmento: str | None) -> str:
    """Determina a classe do ativo BR pelo ticker."""
    # FIIs terminam em 11 e tem nome com FII/FIAGRO
    if ticker.endswith("11"):
        seg_lower = (segmento or "").lower()
        if "fiagro" in seg_lower:
            return "fiagro"
        if "etf" in seg_lower or "metais" in seg_lower or "ouro" in seg_lower:
            return "etf"
        # Default para 11 = FII
        return "fii"
    # Acoes BR terminam em 3 ou 4
    if ticker[-1] in ("3", "4", "5", "6"):
        return "acao"
    return "acao"  # fallback


def _tipo_br(ticker: str, classe: str) -> str:
    if classe == "fii":
        return "fii"
    if classe == "fiagro":
        return "fiagro"
    if classe == "etf":
        return "etf_br"
    return "acao_br"


def _classificar_eua(ticker: str, segmento: str | None) -> str:
    seg_lower = (segmento or "").lower()
    if "reit" in seg_lower:
        return "reit"
    if "etf" in seg_lower:
        return "etf"
    return "acao"


def _tipo_eua(ticker: str, classe: str) -> str:
    if classe == "reit":
        return "reit"
    if classe == "etf":
        return "etf_eua"
    return "acao_eua"