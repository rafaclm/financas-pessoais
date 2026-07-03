"""
Modo Explorador: le as abas anuais (2024/2025/2026) e retorna
o que encontrou, SEM inserir nada no banco.

Permite validar a estrutura antes de importar.
"""
from openpyxl.workbook import Workbook
from loguru import logger
from app.services.importacao.leitor_excel import (
    encontrar_aba, ler_aba_como_lista
)
from app.services.importacao.importacao_base import parse_numero


# Categorias conhecidas e seu tipo (receita/despesa/ignorar)
CATEGORIAS_RECEITA = {"Adiantamento", "Salário", "Salario", "Bônus", "Bonus", "13º", "13o"}
CATEGORIAS_DESPESA = {
    "Investimento", "Extras", "Escola", "Financiamento", "Net"
}
CATEGORIAS_ESPECIAIS = {"Cartão", "Cartao", "Combustível", "Combustivel"}

# Contas conhecidas (Bloco 2 - Detalhes)
CONTAS_BLOCO2 = {
    "Itaú C/C", "Itau C/C", "Itaú Inv", "Itau Inv",
    "Itaú Cartão", "Itau Cartao",
    "Bradesco C/C", "Bradesco Cartão", "Bradesco Cartao",
    "Nomad", "Avenue", "Outros (ML, etc.)", "Outros (ML, etc)",
    "Outros"
}

# Investimentos do Bloco 5
INVESTIMENTOS_BLOCO5 = {
    "Renda Variável", "Renda Variavel",
    "Previdência", "Previdencia",
    "Cripto", "FGTS"
}

MESES_NOMES = {
    "Janeiro": 1, "Fevereiro": 2, "Março": 3, "Marco": 3, "Abril": 4,
    "Maio": 5, "Junho": 6, "Julho": 7, "Agosto": 8,
    "Setembro": 9, "Outubro": 10, "Novembro": 11, "Dezembro": 12,
}


def explorar_aba_anual(wb: Workbook, nome_aba: str) -> dict:
    """
    Le a aba do ano e retorna um relatorio detalhado do que encontrou.
    Nao escreve no banco.
    """
    if not encontrar_aba(wb, nome_aba):
        return {"erro": f"Aba '{nome_aba}' nao encontrada"}

    linhas = ler_aba_como_lista(wb, nome_aba, max_linhas=100)

    relatorio = {
        "aba": nome_aba,
        "total_linhas_lidas": len(linhas),
        "mapeamento_meses": {},
        "bloco_1_movimentos": {
            "categorias_encontradas": [],
            "amostras": [],
        },
        "bloco_2_contas": {
            "contas_encontradas": [],
            "amostras": [],
        },
        "bloco_3_extras": {
            "itens_encontrados": [],
            "amostras": [],
        },
        "bloco_4_combustivel": {
            "dias_e_valores": [],
        },
        "bloco_5_investimentos": {
            "categorias_encontradas": [],
            "amostras": [],
        },
    }

    # ============================================================
    # PASSO 1: Identificar em quais colunas estao os meses
    # Os meses estao na linha 3 (indice 2) baseado no print
    # ============================================================
    mapeamento_meses = {}
    if len(linhas) > 2:
        linha_meses = linhas[2]  # linha 3 = indice 2
        for col_idx, valor in enumerate(linha_meses):
            if valor and isinstance(valor, str):
                nome_norm = str(valor).strip()
                if nome_norm in MESES_NOMES:
                    mes_num = MESES_NOMES[nome_norm]
                    mapeamento_meses[mes_num] = col_idx
    relatorio["mapeamento_meses"] = {
        f"Mes {k}": f"coluna indice {v} (Excel col {_col_letra(v)})"
        for k, v in mapeamento_meses.items()
    }

    # ============================================================
    # BLOCO 1: Movimentacoes mensais (linhas 4-14 aprox)
    # Coluna B (indice 1) tem o nome da categoria
    # ============================================================
    for i, linha in enumerate(linhas[:20]):
        if i < 3 or i > 16:  # focar nas linhas de movimentacoes
            continue
        if len(linha) < 2:
            continue
        nome_categoria = linha[1]  # coluna B
        if not nome_categoria or not isinstance(nome_categoria, str):
            continue
        nome_limpo = str(nome_categoria).strip()
        # Remove prefixos tipo "(5)", "(15)", "(17)"
        if nome_limpo.startswith("("):
            partes = nome_limpo.split(")", 1)
            if len(partes) > 1:
                nome_limpo = partes[1].strip()

        # E uma categoria conhecida?
        eh_receita = nome_limpo in CATEGORIAS_RECEITA
        eh_despesa = nome_limpo in CATEGORIAS_DESPESA
        eh_especial = nome_limpo in CATEGORIAS_ESPECIAIS

        if not (eh_receita or eh_despesa or eh_especial):
            continue

        tipo = "receita" if eh_receita else ("despesa" if eh_despesa else "especial")
        valores_meses = {}
        for mes_num, col_idx in mapeamento_meses.items():
            if col_idx < len(linha):
                valor = parse_numero(linha[col_idx])
                if valor is not None and valor != 0:
                    valores_meses[mes_num] = valor

        relatorio["bloco_1_movimentos"]["categorias_encontradas"].append({
            "linha_excel": i + 1,
            "categoria": nome_limpo,
            "categoria_original": nome_categoria,
            "tipo": tipo,
            "valores_por_mes": valores_meses,
            "total_meses_com_valor": len(valores_meses),
        })

    # Pega 3 amostras de meses para validacao
    amostras_meses = list(mapeamento_meses.items())[:3]
    for mes_num, col_idx in amostras_meses:
        amostra = []
        for item in relatorio["bloco_1_movimentos"]["categorias_encontradas"]:
            if mes_num in item["valores_por_mes"]:
                amostra.append({
                    "categoria": item["categoria"],
                    "tipo": item["tipo"],
                    "valor": item["valores_por_mes"][mes_num],
                })
        relatorio["bloco_1_movimentos"]["amostras"].append({
            f"mes_{mes_num}": amostra
        })

    # ============================================================
    # BLOCO 2: Contas (linhas 22-29 aprox)
    # Coluna B (indice 1) tem o nome da conta
    # ============================================================
    for i, linha in enumerate(linhas[:35]):
        if i < 21 or i > 30:
            continue
        if len(linha) < 2:
            continue
        nome_conta = linha[1]
        if not nome_conta or not isinstance(nome_conta, str):
            continue
        nome_limpo = str(nome_conta).strip()

        # Match aproximado com as contas conhecidas
        encontrou = False
        for conta_padrao in CONTAS_BLOCO2:
            if conta_padrao.lower() in nome_limpo.lower() or nome_limpo.lower() in conta_padrao.lower():
                encontrou = True
                nome_limpo = conta_padrao  # padroniza
                break

        if not encontrou:
            continue

        saldos_meses = {}
        for mes_num, col_idx in mapeamento_meses.items():
            if col_idx < len(linha):
                valor = parse_numero(linha[col_idx])
                if valor is not None and valor != 0:
                    saldos_meses[mes_num] = valor

        relatorio["bloco_2_contas"]["contas_encontradas"].append({
            "linha_excel": i + 1,
            "conta": nome_limpo,
            "saldos_por_mes": saldos_meses,
            "total_meses_com_saldo": len(saldos_meses),
        })

    # Amostra de janeiro
    if 1 in mapeamento_meses:
        amostra = []
        for item in relatorio["bloco_2_contas"]["contas_encontradas"]:
            if 1 in item["saldos_por_mes"]:
                amostra.append({
                    "conta": item["conta"],
                    "saldo_janeiro": item["saldos_por_mes"][1],
                })
        relatorio["bloco_2_contas"]["amostras"].append({"janeiro": amostra})

    # ============================================================
    # BLOCO 3: Extras detalhados (linhas 31-37 aprox)
    # ============================================================
    extras_por_mes = {}
    for i, linha in enumerate(linhas[:45]):
        if i < 30 or i > 40:
            continue
        if len(linha) < 2:
            continue
        for mes_num, col_idx in mapeamento_meses.items():
            if col_idx >= len(linha) or col_idx + 1 >= len(linha):
                continue
            # Coluna do mes = descricao do extra
            desc = linha[col_idx]
            valor = linha[col_idx + 1] if col_idx + 1 < len(linha) else None
            if desc and isinstance(desc, str) and desc.strip():
                desc_str = str(desc).strip()
                valor_num = parse_numero(valor)
                if valor_num is not None and valor_num != 0:
                    if mes_num not in extras_por_mes:
                        extras_por_mes[mes_num] = []
                    extras_por_mes[mes_num].append({
                        "descricao": desc_str,
                        "valor": valor_num,
                        "linha_excel": i + 1,
                    })

    relatorio["bloco_3_extras"]["itens_encontrados"] = extras_por_mes

    # Amostra do primeiro mes com dados
    for mes_num in sorted(extras_por_mes.keys())[:2]:
        relatorio["bloco_3_extras"]["amostras"].append({
            f"mes_{mes_num}": extras_por_mes[mes_num]
        })

    # ============================================================
    # BLOCO 4: Combustivel (linhas 40-44 aprox)
    # Cada mes: pares Dia / Valor
    # ============================================================
    combustivel_por_mes = {}
    for i, linha in enumerate(linhas[:48]):
        if i < 39 or i > 46:
            continue
        if len(linha) < 2:
            continue
        for mes_num, col_idx in mapeamento_meses.items():
            if col_idx >= len(linha) or col_idx + 1 >= len(linha):
                continue
            dia = parse_numero(linha[col_idx])
            valor = parse_numero(linha[col_idx + 1])
            if dia is not None and valor is not None and dia > 0 and valor > 0:
                if mes_num not in combustivel_por_mes:
                    combustivel_por_mes[mes_num] = []
                combustivel_por_mes[mes_num].append({
                    "dia": int(dia),
                    "valor": valor,
                    "linha_excel": i + 1,
                })

    relatorio["bloco_4_combustivel"]["dias_e_valores"] = combustivel_por_mes

    # ============================================================
    # BLOCO 5: Investimentos (linhas 52-73 aprox)
    # ============================================================
    for i, linha in enumerate(linhas[:80]):
        if i < 50 or i > 75:
            continue
        if len(linha) < 2:
            continue

        # Procura titulos (Renda Variavel, Previdencia, Cripto, FGTS)
        titulo_categoria = None
        # Verifica varias colunas porque pode estar em diferentes posicoes
        for col_check in range(0, min(5, len(linha))):
            valor = linha[col_check]
            if valor and isinstance(valor, str):
                v_limpo = str(valor).strip()
                if v_limpo in INVESTIMENTOS_BLOCO5:
                    titulo_categoria = v_limpo
                    break

        # Verifica se essa linha tem "Saldo" na coluna B
        nome_linha = linha[1] if len(linha) > 1 else None
        if not nome_linha or not isinstance(nome_linha, str):
            continue

        nome_limpo = str(nome_linha).strip()
        if nome_limpo != "Saldo":
            continue

        # Procura a categoria desse bloco olhando linhas anteriores
        categoria_encontrada = None
        for j in range(max(0, i - 5), i):
            linha_anterior = linhas[j]
            for col_check in range(0, min(5, len(linha_anterior))):
                v = linha_anterior[col_check]
                if v and isinstance(v, str) and str(v).strip() in INVESTIMENTOS_BLOCO5:
                    categoria_encontrada = str(v).strip()
                    break
            if categoria_encontrada:
                break

        if not categoria_encontrada:
            continue

        saldos_meses = {}
        for mes_num, col_idx in mapeamento_meses.items():
            if col_idx < len(linha):
                valor = parse_numero(linha[col_idx])
                if valor is not None and valor != 0:
                    saldos_meses[mes_num] = valor

        relatorio["bloco_5_investimentos"]["categorias_encontradas"].append({
            "linha_excel": i + 1,
            "categoria": categoria_encontrada,
            "saldos_por_mes": saldos_meses,
            "total_meses_com_saldo": len(saldos_meses),
        })

    # Amostra de janeiro
    if 1 in mapeamento_meses:
        amostra = []
        for item in relatorio["bloco_5_investimentos"]["categorias_encontradas"]:
            if 1 in item["saldos_por_mes"]:
                amostra.append({
                    "categoria": item["categoria"],
                    "saldo_janeiro": item["saldos_por_mes"][1],
                })
        relatorio["bloco_5_investimentos"]["amostras"].append({"janeiro": amostra})

    return relatorio


def _col_letra(col_idx: int) -> str:
    """Converte indice de coluna (0-based) em letra Excel (A, B, ..., AA, AB, ...)."""
    letra = ""
    idx = col_idx
    while True:
        letra = chr(ord("A") + (idx % 26)) + letra
        idx = idx // 26 - 1
        if idx < 0:
            break
    return letra