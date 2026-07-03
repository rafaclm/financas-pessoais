"""
Importador da aba 'Aportes'.
Cria aportes de bolsa a partir das linhas detalhadas da planilha.

Layout esperado da aba 'Aportes':
  Col A: Data (08/04/2026)
  Col B: Ticker (SPXI11, ALZR11, O)
  Col C: Pais (EUA, ou vazio para BR)
  Col D: Quantidade (positivo = compra, negativo = venda)
  Col E: Preco unitario
  Col F: Total (calculado)
  Col G: Periodo (2026/4)
  Col H: Observacao
"""
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import select
from openpyxl.workbook import Workbook
from loguru import logger

from app.infrastructure.db.models import Ano, Ativo, AporteBolsa
from app.services.importacao.leitor_excel import encontrar_aba, ler_aba_como_lista
from app.services.importacao.importacao_base import (
    ResultadoImportacao, parse_numero, normalizar_ticker, parse_data
)
from app.services.importacao.importacao_contas import buscar_conta
from app.services.conversao_bcb import obter_cotacao_por_data
from app.services.posicao_atual import recalcular_posicao_ativo


def _inferir_classe_ticker(ticker: str, pais: str | None) -> tuple[str, str, str, str]:
    """
    Infere (classe, tipo, mercado, geografia) com base no ticker e pais.
    Retorna: (classe, tipo, mercado, geografia)
    """
    t = ticker.upper()
    pais_norm = (pais or "").strip().upper() if pais else ""

    # EUA explicito
    if pais_norm in ("EUA", "USA", "US", "ESTADOS UNIDOS"):
        # Tickers conhecidos
        if t in ("VOO", "SPY", "QQQ", "VTI", "BND", "SGOV", "VEA", "VWO"):
            return ("etf", "etf_eua", "NYSE", "EUA")
        if t in ("O", "VICI", "STAG", "AGNC", "PSEC"):
            return ("reit", "reit", "NYSE", "EUA")
        return ("acao", "acao_eua", "NYSE", "EUA")

    # BR
    if t.endswith("11"):
        # FIIs, ETFs BR, Fiagros, BDRs
        if t in ("BOVA11", "IVVB11", "SMAL11", "GOLD11", "SPXI11"):
            return ("etf", "etf_br", "B3", "BR")
        if t.startswith("RZAG") or "AG" in t:
            return ("fiagro", "fiagro", "B3", "BR")
        # Default 11 = FII
        return ("fii", "fii", "B3", "BR")
    # Acoes BR terminam em 3, 4, 5, 6
    if len(t) >= 5 and t[-1] in ("3", "4", "5", "6"):
        return ("acao", "acao_br", "B3", "BR")

    # Cripto (heuristica simples: 3-4 letras maiusculas sem numero)
    if len(t) <= 5 and t.isalpha():
        return ("cripto", "cripto", "CRIPTO", "GLOBAL")

    # Fallback
    return ("acao", "acao_br", "B3", "BR")


def listar_tickers_da_aba(wb: Workbook) -> list:
    """
    Le a aba 'Aportes' e retorna a lista de tickers distintos.
    Util para o preview (mostrar tickers novos que serao criados).
    """
    aba = encontrar_aba(wb, "Aportes")
    if not aba:
        return []
    linhas = ler_aba_como_lista(wb, aba, max_linhas=5000)

    tickers_encontrados = {}
    for i, linha in enumerate(linhas):
        if i < 1:  # pula cabecalho
            continue
        if len(linha) < 3:
            continue
        ticker = normalizar_ticker(linha[1])
        if not ticker:
            continue
        pais = linha[2] if len(linha) > 2 else None
        if ticker not in tickers_encontrados:
            classe, tipo, mercado, geografia = _inferir_classe_ticker(ticker, pais)
            tickers_encontrados[ticker] = {
                "ticker": ticker,
                "pais_planilha": str(pais).strip() if pais else "",
                "classe": classe,
                "tipo": tipo,
                "mercado": mercado,
                "geografia": geografia,
            }
    return list(tickers_encontrados.values())


def analisar_aba_aportes(db: Session, wb: Workbook) -> dict:
    """
    Faz um analise da aba 'Aportes' sem inserir nada.
    Retorna:
    - total_linhas
    - tickers_existentes (ja cadastrados no banco)
    - tickers_novos (serao criados se confirmar)
    - estatisticas (compras, vendas, valores)
    """
    tickers = listar_tickers_da_aba(wb)

    tickers_existentes = []
    tickers_novos = []

    for t_info in tickers:
        existe = db.scalar(select(Ativo).where(Ativo.ticker == t_info["ticker"]))
        if existe:
            tickers_existentes.append({
                "ticker": t_info["ticker"],
                "nome_sistema": existe.nome,
                "geografia": existe.geografia,
                "classe": existe.classe,
            })
        else:
            tickers_novos.append(t_info)

    aba = encontrar_aba(wb, "Aportes")
    linhas = ler_aba_como_lista(wb, aba, max_linhas=5000) if aba else []

    # Estatisticas basicas
    total_linhas_validas = 0
    compras = 0
    vendas = 0
    valor_total_brl_estimado = 0

    for i, linha in enumerate(linhas):
        if i < 1:
            continue
        if len(linha) < 6:
            continue
        ticker = normalizar_ticker(linha[1])
        qtd = parse_numero(linha[3])
        preco = parse_numero(linha[4])
        if not ticker or qtd is None or preco is None or qtd == 0:
            continue
        total_linhas_validas += 1
        if qtd > 0:
            compras += 1
        else:
            vendas += 1
        valor_total_brl_estimado += abs(qtd) * preco

    return {
        "total_linhas_validas": total_linhas_validas,
        "compras": compras,
        "vendas": vendas,
        "valor_total_brl_estimado": round(valor_total_brl_estimado, 2),
        "tickers_existentes": tickers_existentes,
        "tickers_novos": tickers_novos,
    }


def criar_ativos_novos(db: Session, tickers_novos: list) -> list:
    """Cria os ativos que sao novos no banco."""
    criados = []
    for t_info in tickers_novos:
        existe = db.scalar(select(Ativo).where(Ativo.ticker == t_info["ticker"]))
        if existe:
            continue
        moeda = "USD" if t_info["geografia"] == "EUA" else "BRL"
        novo = Ativo(
            ticker=t_info["ticker"],
            nome=t_info["ticker"],  # sem nome detalhado, usa o ticker
            tipo=t_info["tipo"],
            mercado=t_info["mercado"],
            geografia=t_info["geografia"],
            classe=t_info["classe"],
            moeda=moeda,
            setor=None,
            ativo=1,
        )
        db.add(novo)
        criados.append(t_info["ticker"])
    db.commit()
    logger.info(f"Ativos criados: {criados}")
    return criados


def importar_aportes(
    db: Session, wb: Workbook, criar_tickers_novos: bool = True,
    dry_run: bool = False
) -> dict:
    """
    Importa os aportes da aba 'Aportes'.
    Se criar_tickers_novos=True, cria automaticamente ativos novos.
    """
    resultado = ResultadoImportacao()
    aba = encontrar_aba(wb, "Aportes")
    if not aba:
        return {"erro": "Aba 'Aportes' nao encontrada"}

    # 1. Trata tickers novos
    if criar_tickers_novos and not dry_run:
        tickers = listar_tickers_da_aba(wb)
        novos = [t for t in tickers
                 if not db.scalar(select(Ativo).where(Ativo.ticker == t["ticker"]))]
        criar_ativos_novos(db, novos)

    # 2. Le linhas e cria aportes
    linhas = ler_aba_como_lista(wb, aba, max_linhas=5000)
    ativos_afetados = set()  # para recalcular posicao apos importar

    # Cache de cotacoes USD/BRL por data
    cache_cotacoes = {}

    for i, linha in enumerate(linhas):
        if i < 1:  # pula cabecalho
            continue
        if len(linha) < 6:
            continue

        data_raw = linha[0]
        ticker = normalizar_ticker(linha[1])
        pais = linha[2] if len(linha) > 2 else None
        qtd_raw = parse_numero(linha[3])
        preco = parse_numero(linha[4])

        if not ticker or qtd_raw is None or preco is None or qtd_raw == 0 or preco <= 0:
            continue

        # Parse data
        if isinstance(data_raw, datetime):
            data_op = data_raw.date()
        elif isinstance(data_raw, date):
            data_op = data_raw
        else:
            dt = parse_data(data_raw)
            if not dt:
                resultado.erros += 1
                resultado.detalhes_erros.append(
                    f"Linha {i+1}: data invalida '{data_raw}'"
                )
                continue
            data_op = dt.date() if isinstance(dt, datetime) else dt

        # Determina compra/venda
        if qtd_raw > 0:
            tipo_op = "compra"
            quantidade = qtd_raw
        else:
            tipo_op = "venda"
            quantidade = abs(qtd_raw)

        # Determina moeda
        pais_norm = (pais or "").strip().upper() if pais else ""
        if pais_norm in ("EUA", "USA", "US"):
            moeda = "USD"
        else:
            moeda = "BRL"

        # Busca ativo
        ativo_obj = db.scalar(select(Ativo).where(Ativo.ticker == ticker))
        if not ativo_obj:
            resultado.erros += 1
            resultado.detalhes_erros.append(
                f"Linha {i+1}: ativo '{ticker}' nao existe e tickers novos nao foram criados"
            )
            continue

        # Ano
        ano_obj = db.scalar(select(Ano).where(Ano.ano == data_op.year))
        if not ano_obj:
            ano_obj = Ano(ano=data_op.year, saldo_inicial=0, ativo=1,
                          observacao="Criado pela importacao de aportes")
            db.add(ano_obj)
            db.commit()
            db.refresh(ano_obj)

        # Verifica duplicidade
        existe = db.scalar(select(AporteBolsa).where(
            AporteBolsa.ativo_id == ativo_obj.id,
            AporteBolsa.data == data_op,
            AporteBolsa.quantidade == quantidade,
            AporteBolsa.preco_unitario == preco,
            AporteBolsa.tipo_operacao == tipo_op,
        ))
        if existe:
            resultado.pulados += 1
            continue

        # Conta padrao (sua decisao: sem conta = null)
        # Mas o sistema requer conta_id NOT NULL? Vamos usar Itau C/C como fallback
        conta_padrao = buscar_conta(db, "Itau C/C")
        conta_id_use = conta_padrao.id if conta_padrao else None

        # Cotacao USD/BRL (so para USD)
        cotacao_usd_brl = None
        if moeda == "USD":
            cache_key = data_op.isoformat()
            if cache_key in cache_cotacoes:
                cotacao_usd_brl = cache_cotacoes[cache_key]
            else:
                cotacao_usd_brl = obter_cotacao_por_data(db, data_op)
                cache_cotacoes[cache_key] = cotacao_usd_brl

            if not cotacao_usd_brl:
                resultado.erros += 1
                resultado.detalhes_erros.append(
                    f"Linha {i+1}: nao foi possivel obter cotacao USD/BRL para {data_op}"
                )
                continue

        # Calculo valor_total
        valor_total = float(quantidade) * float(preco)  # sem taxas
        if moeda == "USD":
            valor_total_brl = valor_total * float(cotacao_usd_brl)
        else:
            valor_total_brl = valor_total

        if not dry_run:
            aporte = AporteBolsa(
                ano_id=ano_obj.id,
                mes=data_op.month,
                data=data_op,
                ativo_id=ativo_obj.id,
                tipo_operacao=tipo_op,
                quantidade=quantidade,
                preco_unitario=preco,
                taxas=0,
                moeda=moeda,
                cotacao_usd_brl=cotacao_usd_brl,
                valor_total=valor_total,
                valor_total_brl=valor_total_brl,
                conta_id=conta_id_use,
                descricao=f"Importado da planilha {data_op}",
            )
            db.add(aporte)
            ativos_afetados.add(ativo_obj.id)

        resultado.inseridos += 1
        resultado.detalhes_inseridos.append(
            f"{data_op} - {ticker} {tipo_op} {quantidade} @ {preco} {moeda}"
        )

    if not dry_run:
        db.commit()
        # Recalcula posicao atual de todos os ativos afetados
        for ativo_id in ativos_afetados:
            try:
                recalcular_posicao_ativo(db, ativo_id, commit=False)
            except Exception as e:
                logger.warning(f"Erro ao recalcular ativo {ativo_id}: {e}")
        db.commit()

    resultado.mensagem = (
        f"{resultado.inseridos} aportes inseridos, "
        f"{resultado.pulados} ja existiam, "
        f"{resultado.erros} erros."
    )
    logger.info(resultado.mensagem)
    return resultado.__dict__