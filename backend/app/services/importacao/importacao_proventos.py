"""
Importador da aba 'Proventos'.

Layout esperado:
  Col A: Ticker (SANB11, O)
  Col B: Data (07/mai/26)
  Col C: Pais (EUA ou vazio)
  Col D: Tipo (JCP, Rendimento, Dividendo)
  Col E: Valor/cota
  Col F: Quantidade
  Col G: Total (moeda nativa)
  Col H: Total Convertido (em BRL para USD; igual a Total para BRL)
"""
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import select
from openpyxl.workbook import Workbook
from loguru import logger

from app.infrastructure.db.models import Ano, Ativo, Provento
from app.services.importacao.leitor_excel import encontrar_aba, ler_aba_como_lista
from app.services.importacao.importacao_base import (
    ResultadoImportacao, parse_numero, normalizar_ticker, parse_data
)
from app.services.importacao.importacao_aportes import _inferir_classe_ticker


# Mapeamento de tipos da planilha → sistema
TIPO_MAP = {
    "dividendo": "dividendo",
    "dividend": "dividendo",
    "div": "dividendo",
    "jcp": "jcp",
    "juros sobre capital": "jcp",
    "juros sobre capital proprio": "jcp",
    "rendimento": "rendimento",
    "rendimentos": "rendimento",
    "yield": "rendimento",
    "juros_cripto": "juros_cripto",
    "juros cripto": "juros_cripto",
    "stake": "juros_cripto",
    "staking": "juros_cripto",
    "outro": "outro",
    "outros": "outro",
}


def _normalizar_tipo(texto) -> str:
    """Normaliza tipo de provento para o que o sistema aceita."""
    if not texto:
        return "outro"
    s = str(texto).strip().lower()
    s = s.replace("ç", "c").replace("ã", "a").replace("é", "e").replace("õ", "o")
    return TIPO_MAP.get(s, "outro")


def listar_tickers_proventos(wb: Workbook) -> list:
    """Le a aba 'Proventos' e retorna lista de tickers distintos."""
    aba = encontrar_aba(wb, "Proventos")
    if not aba:
        return []
    linhas = ler_aba_como_lista(wb, aba, max_linhas=10000)

    tickers_encontrados = {}
    for i, linha in enumerate(linhas):
        if i < 1:  # pula cabecalho
            continue
        if len(linha) < 3:
            continue
        ticker = normalizar_ticker(linha[0])  # COL A = ticker
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


def analisar_aba_proventos(db: Session, wb: Workbook) -> dict:
    """Analisa a aba 'Proventos' sem inserir nada."""
    tickers = listar_tickers_proventos(wb)
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

    aba = encontrar_aba(wb, "Proventos")
    linhas = ler_aba_como_lista(wb, aba, max_linhas=10000) if aba else []

    total_linhas_validas = 0
    total_brl_estimado = 0
    distribuicao_tipos = {}

    for i, linha in enumerate(linhas):
        if i < 1:
            continue
        if len(linha) < 7:
            continue
        ticker = normalizar_ticker(linha[0])
        total_conv = parse_numero(linha[7]) if len(linha) > 7 else None
        tipo_raw = linha[3] if len(linha) > 3 else None
        if not ticker or total_conv is None or total_conv == 0:
            continue
        total_linhas_validas += 1
        total_brl_estimado += abs(total_conv)
        tipo_norm = _normalizar_tipo(tipo_raw)
        distribuicao_tipos[tipo_norm] = distribuicao_tipos.get(tipo_norm, 0) + 1

    return {
        "total_linhas_validas": total_linhas_validas,
        "total_brl_estimado": round(total_brl_estimado, 2),
        "distribuicao_tipos": distribuicao_tipos,
        "tickers_existentes": tickers_existentes,
        "tickers_novos": tickers_novos,
    }


def criar_ativos_novos_proventos(db: Session, tickers_novos: list) -> list:
    """Cria os ativos que sao novos no banco."""
    criados = []
    for t_info in tickers_novos:
        existe = db.scalar(select(Ativo).where(Ativo.ticker == t_info["ticker"]))
        if existe:
            continue
        moeda = "USD" if t_info["geografia"] == "EUA" else "BRL"
        novo = Ativo(
            ticker=t_info["ticker"],
            nome=t_info["ticker"],
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
    logger.info(f"Ativos criados (proventos): {criados}")
    return criados


def importar_proventos(
    db: Session, wb: Workbook,
    criar_tickers_novos: bool = True,
    dry_run: bool = False
) -> dict:
    """Importa os proventos da aba 'Proventos'."""
    resultado = ResultadoImportacao()
    aba = encontrar_aba(wb, "Proventos")
    if not aba:
        return {"erro": "Aba 'Proventos' nao encontrada"}

    # Cria tickers novos se autorizado
    if criar_tickers_novos and not dry_run:
        tickers = listar_tickers_proventos(wb)
        novos = [t for t in tickers
                 if not db.scalar(select(Ativo).where(Ativo.ticker == t["ticker"]))]
        criar_ativos_novos_proventos(db, novos)

    linhas = ler_aba_como_lista(wb, aba, max_linhas=10000)

    for i, linha in enumerate(linhas):
        if i < 1:  # pula cabecalho
            continue
        if len(linha) < 7:
            continue

        ticker = normalizar_ticker(linha[0])
        data_raw = linha[1]
        pais = linha[2] if len(linha) > 2 else None
        tipo_raw = linha[3] if len(linha) > 3 else None
        valor_cota = parse_numero(linha[4]) if len(linha) > 4 else None
        quantidade = parse_numero(linha[5]) if len(linha) > 5 else None
        total_nativo = parse_numero(linha[6]) if len(linha) > 6 else None
        total_convertido = parse_numero(linha[7]) if len(linha) > 7 else None

        if not ticker or total_nativo is None or total_nativo == 0:
            continue

        # Parse data
        if isinstance(data_raw, datetime):
            data_pgto = data_raw.date()
        elif isinstance(data_raw, date):
            data_pgto = data_raw
        else:
            dt = parse_data(data_raw)
            if not dt:
                resultado.erros += 1
                resultado.detalhes_erros.append(
                    f"Linha {i+1}: data invalida '{data_raw}'"
                )
                continue
            data_pgto = dt.date() if isinstance(dt, datetime) else dt

        # Determina moeda pelo pais
        pais_norm = (pais or "").strip().upper() if pais else ""
        moeda = "USD" if pais_norm in ("EUA", "USA", "US") else "BRL"

        # Tipo
        tipo_norm = _normalizar_tipo(tipo_raw)

        # Busca ativo
        ativo_obj = db.scalar(select(Ativo).where(Ativo.ticker == ticker))
        if not ativo_obj:
            resultado.erros += 1
            resultado.detalhes_erros.append(
                f"Linha {i+1}: ativo '{ticker}' nao existe"
            )
            continue

        # Ano
        ano_obj = db.scalar(select(Ano).where(Ano.ano == data_pgto.year))
        if not ano_obj:
            ano_obj = Ano(ano=data_pgto.year, saldo_inicial=0, ativo=1,
                          observacao="Criado pela importacao de proventos")
            db.add(ano_obj)
            db.commit()
            db.refresh(ano_obj)

        # Decisao 3C: usa Total como valor_liquido (moeda nativa)
        # e Total Convertido como valor_liquido_brl
        # Calcula cotacao implicita se for USD
        valor_liquido = abs(total_nativo)
        if moeda == "USD" and total_convertido:
            valor_liquido_brl = abs(total_convertido)
            cotacao_implicita = (
                valor_liquido_brl / valor_liquido if valor_liquido > 0 else None
            )
        else:
            valor_liquido_brl = valor_liquido  # BRL: igual ao total
            cotacao_implicita = None

        # valor_bruto: como a planilha nao tem bruto, igual ao liquido
        valor_bruto = valor_liquido

        # quantidade_cotas
        qtd_cotas_validas = None
        if quantidade is not None and quantidade > 0:
            qtd_cotas_validas = float(quantidade)

        # Verifica duplicidade (mesma data + ativo + tipo + valor)
        existe = db.scalar(select(Provento).where(
            Provento.ativo_id == ativo_obj.id,
            Provento.data == data_pgto,
            Provento.tipo == tipo_norm,
            Provento.valor_liquido == valor_liquido,
        ))
        if existe:
            resultado.pulados += 1
            continue

        if not dry_run:
            prov = Provento(
                ano_id=ano_obj.id,
                mes=data_pgto.month,
                data=data_pgto,
                ativo_id=ativo_obj.id,
                tipo=tipo_norm,
                valor_bruto=valor_bruto,
                valor_liquido=valor_liquido,
                moeda=moeda,
                cotacao_usd_brl=cotacao_implicita,
                valor_liquido_brl=valor_liquido_brl,
                conta_id=None,
                descricao=f"Importado da planilha {data_pgto}",
                quantidade_cotas=qtd_cotas_validas,
            )
            db.add(prov)

        resultado.inseridos += 1
        resultado.detalhes_inseridos.append(
            f"{data_pgto} - {ticker} {tipo_norm} - "
            f"{valor_liquido} {moeda} (BRL: {valor_liquido_brl:.2f})"
        )

    if not dry_run:
        db.commit()

    resultado.mensagem = (
        f"{resultado.inseridos} proventos inseridos, "
        f"{resultado.pulados} ja existiam, "
        f"{resultado.erros} erros."
    )
    logger.info(resultado.mensagem)
    return resultado.__dict__