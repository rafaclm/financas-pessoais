"""
Importador de movimentacoes mensais das abas anuais (2024, 2025, 2026).
"""
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import select
from openpyxl.workbook import Workbook
from loguru import logger

from app.infrastructure.db.models import (
    Ano, LancamentoReceita, LancamentoDespesa, LancamentoCombustivel,
    PagamentoCartao, CategoriaDespesa, SaldoConta, SaldoInvestimento
)
from app.services.importacao.leitor_excel import encontrar_aba, ler_aba_como_lista
from app.services.importacao.importacao_base import (
    ResultadoImportacao, parse_numero
)
from app.services.importacao.importacao_contas import (
    buscar_categoria_receita, buscar_categoria_despesa,
    buscar_conta, buscar_cartao, buscar_produto,
)


def _normalizar_mes(texto: str) -> str | None:
    """🆕 Normaliza nome do mes (remove acentos, lowercase, strip)."""
    if not texto or not isinstance(texto, str):
        return None
    s = str(texto).strip().lower()
    # Remove acentos comuns
    s = s.replace("ç", "c").replace("ã", "a").replace("á", "a").replace("é", "e")
    s = s.replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ô", "o")
    mapeamento = {
        "janeiro": 1, "fevereiro": 2, "marco": 3, "abril": 4,
        "maio": 5, "junho": 6, "julho": 7, "agosto": 8,
        "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12,
    }
    return mapeamento.get(s)


CATEGORIAS_RECEITA = {
    "Adiantamento": "Adiantamento",
    "Salario": "Salario", "Salário": "Salario",
    "Bonus": "Bonus", "Bônus": "Bonus",
    "13o": "13o", "13º": "13o",
}
CATEGORIAS_DESPESA = {
    "Investimento": "Investimento",
    "Extras": "Extras",
    "Escola": "Escola",
    "Financiamento": "Financiamento",
    "Net": "Net",
}

CONTAS_BLOCO2_NOMES = {
    "Itaú C/C": "Itau C/C", "Itau C/C": "Itau C/C",
    "Itaú Inv": "Itau Inv", "Itau Inv": "Itau Inv",
    "Bradesco C/C": "Bradesco C/C",
    "Nomad": "Nomad", "Avenue": "Avenue",
    "Outros (ML, etc.)": "Mercado Livre",
    "Outros (ML, etc)": "Mercado Livre",
    "Outros": "Mercado Livre",
}

CONTAS_IGNORAR = {"Itaú Cartão", "Itau Cartao", "Bradesco Cartão", "Bradesco Cartao"}


def garantir_ano(db: Session, ano_num: int) -> Ano:
    """Cria o ano se nao existir."""
    ano = db.scalar(select(Ano).where(Ano.ano == ano_num))
    if not ano:
        ano = Ano(ano=ano_num, saldo_inicial=0, ativo=1,
                  observacao=f"Criado pela importacao")
        db.add(ano)
        db.commit()
        db.refresh(ano)
    return ano


def mapear_meses_da_aba(linhas: list) -> dict:
    """🆕 Le linha 3 (indice 2) e retorna {mes_num: col_idx} — agora robusto."""
    mapeamento = {}
    if len(linhas) > 2:
        linha_meses = linhas[2]
        for col_idx, valor in enumerate(linha_meses):
            mes_num = _normalizar_mes(valor)
            if mes_num:
                mapeamento[mes_num] = col_idx
    logger.info(f"Mapeamento meses encontrado: {mapeamento}")
    return mapeamento


def importar_movimentos_ano(
    db: Session, wb: Workbook, ano_num: int,
    blocos: list, dry_run: bool = False
) -> dict:
    """Importa as movimentacoes de uma aba anual."""
    nome_aba = str(ano_num)
    if not encontrar_aba(wb, nome_aba):
        return {"erro": f"Aba '{nome_aba}' nao encontrada"}

    linhas = ler_aba_como_lista(wb, nome_aba, max_linhas=100)
    mapa_meses = mapear_meses_da_aba(linhas)

    if not mapa_meses:
        return {"erro": "Nao foi possivel identificar os meses na aba"}

    if len(mapa_meses) < 12:
        logger.warning(
            f"⚠️ Aba {nome_aba}: apenas {len(mapa_meses)} de 12 meses mapeados! "
            f"Meses encontrados: {list(mapa_meses.keys())}"
        )

    ano_obj = garantir_ano(db, ano_num)
    resultados = {}

    # ============================================================
    # BLOCO 1: Receitas e Despesas (linhas 4-14 aprox)
    # ============================================================
    if "receitas_despesas" in blocos:
        resultados["receitas"] = ResultadoImportacao()
        resultados["despesas"] = ResultadoImportacao()

        conta_padrao = buscar_conta(db, "Itau C/C")
        if not conta_padrao:
            return {"erro": "Conta 'Itau C/C' nao encontrada"}

        for i, linha in enumerate(linhas[:20]):
            if i < 3 or i > 16:
                continue
            if len(linha) < 2:
                continue
            nome_cat = linha[1]
            if not nome_cat or not isinstance(nome_cat, str):
                continue

            nome_limpo = str(nome_cat).strip()
            if nome_limpo.startswith("("):
                partes = nome_limpo.split(")", 1)
                if len(partes) > 1:
                    nome_limpo = partes[1].strip()

            cat_recpta = CATEGORIAS_RECEITA.get(nome_limpo)
            cat_desp = CATEGORIAS_DESPESA.get(nome_limpo)

            if cat_recpta:
                # === RECEITAS ===
                cat_obj = buscar_categoria_receita(db, cat_recpta)
                if not cat_obj:
                    resultados["receitas"].erros += 1
                    resultados["receitas"].detalhes_erros.append(
                        f"Categoria '{cat_recpta}' nao encontrada"
                    )
                    continue

                for mes_num, col_idx in mapa_meses.items():
                    if col_idx >= len(linha):
                        continue
                    valor_raw = parse_numero(linha[col_idx])
                    if valor_raw is None or valor_raw == 0:
                        continue
                    # 🆕 FIX: receita usa abs (sempre positivo)
                    valor = abs(valor_raw)

                    existe = db.scalar(select(LancamentoReceita).where(
                        LancamentoReceita.ano_id == ano_obj.id,
                        LancamentoReceita.mes == mes_num,
                        LancamentoReceita.categoria_id == cat_obj.id,
                        LancamentoReceita.valor == valor,
                    ))
                    if existe:
                        resultados["receitas"].pulados += 1
                        continue

                    if not dry_run:
                        rec = LancamentoReceita(
                            ano_id=ano_obj.id, mes=mes_num,
                            categoria_id=cat_obj.id,
                            conta_id=conta_padrao.id,
                            valor=valor,
                            descricao=f"Importado da planilha {ano_num}",
                            recorrente=1 if cat_recpta in ("Adiantamento", "Salario") else 0,
                        )
                        db.add(rec)
                    resultados["receitas"].inseridos += 1
                    resultados["receitas"].detalhes_inseridos.append(
                        f"{cat_recpta} - {ano_num}/{mes_num} = R$ {valor:.2f}"
                    )

            elif cat_desp:
                # === DESPESAS === 🆕 FIX CRÍTICO: usa abs() para aceitar positivo OU negativo
                cat_obj = buscar_categoria_despesa(db, cat_desp)
                if not cat_obj:
                    resultados["despesas"].erros += 1
                    resultados["despesas"].detalhes_erros.append(
                        f"Categoria '{cat_desp}' nao encontrada"
                    )
                    continue

                for mes_num, col_idx in mapa_meses.items():
                    if col_idx >= len(linha):
                        continue
                    valor_raw = parse_numero(linha[col_idx])
                    if valor_raw is None or valor_raw == 0:
                        continue
                    # 🆕 FIX 1: SEMPRE usa valor absoluto para despesa
                    valor = abs(valor_raw)

                    existe = db.scalar(select(LancamentoDespesa).where(
                        LancamentoDespesa.ano_id == ano_obj.id,
                        LancamentoDespesa.mes == mes_num,
                        LancamentoDespesa.categoria_id == cat_obj.id,
                        LancamentoDespesa.valor == valor,
                        LancamentoDespesa.auto_pagamento_cartao == 0,
                    ))
                    if existe:
                        resultados["despesas"].pulados += 1
                        continue

                    if not dry_run:
                        desp = LancamentoDespesa(
                            ano_id=ano_obj.id, mes=mes_num,
                            categoria_id=cat_obj.id,
                            origem_tipo="conta", conta_id=conta_padrao.id,
                            valor=valor,
                            descricao=f"Importado da planilha {ano_num}",
                            recorrente=1 if cat_desp in ("Escola", "Financiamento", "Net") else 0,
                        )
                        db.add(desp)
                    resultados["despesas"].inseridos += 1
                    resultados["despesas"].detalhes_inseridos.append(
                        f"{cat_desp} - {ano_num}/{mes_num} = R$ {valor:.2f}"
                    )

        if not dry_run:
            db.commit()
        resultados["receitas"].mensagem = (
            f"{resultados['receitas'].inseridos} receitas inseridas, "
            f"{resultados['receitas'].pulados} ja existiam"
        )
        resultados["despesas"].mensagem = (
            f"{resultados['despesas'].inseridos} despesas inseridas, "
            f"{resultados['despesas'].pulados} ja existiam"
        )

    # ============================================================
    # BLOCO 2: Saldos de Contas (linhas 22-29)
    # ============================================================
    if "saldos_contas" in blocos:
        resultados["saldos_contas"] = ResultadoImportacao()

        for i, linha in enumerate(linhas[:35]):
            if i < 21 or i > 30:
                continue
            if len(linha) < 2:
                continue
            nome_conta = linha[1]
            if not nome_conta or not isinstance(nome_conta, str):
                continue
            nome_limpo = str(nome_conta).strip()

            if nome_limpo in CONTAS_IGNORAR:
                continue

            nome_sistema = None
            for k, v in CONTAS_BLOCO2_NOMES.items():
                if k.lower() == nome_limpo.lower():
                    nome_sistema = v
                    break
            if not nome_sistema:
                continue

            conta_obj = buscar_conta(db, nome_sistema)
            if not conta_obj:
                resultados["saldos_contas"].erros += 1
                continue

            for mes_num, col_idx in mapa_meses.items():
                if col_idx >= len(linha):
                    continue
                valor = parse_numero(linha[col_idx])
                # Saldo de conta: aceita positivo apenas
                if valor is None or valor <= 0:
                    continue

                existe = db.scalar(select(SaldoConta).where(
                    SaldoConta.ano_id == ano_obj.id,
                    SaldoConta.mes == mes_num,
                    SaldoConta.conta_id == conta_obj.id,
                ))
                if existe:
                    resultados["saldos_contas"].pulados += 1
                    continue

                if not dry_run:
                    saldo = SaldoConta(
                        ano_id=ano_obj.id, mes=mes_num,
                        conta_id=conta_obj.id,
                        saldo=valor, saldo_brl=valor,
                    )
                    db.add(saldo)
                resultados["saldos_contas"].inseridos += 1

        if not dry_run:
            db.commit()
        resultados["saldos_contas"].mensagem = (
            f"{resultados['saldos_contas'].inseridos} saldos inseridos"
        )

    # ============================================================
    # BLOCO 3: Extras detalhados (linhas 31-37)
    # ============================================================
    if "extras" in blocos:
        resultados["extras"] = ResultadoImportacao()

        conta_padrao = buscar_conta(db, "Itau C/C")
        cat_extras_desp = buscar_categoria_despesa(db, "Extras")
        cat_extras_rec = buscar_categoria_receita(db, "Extras")

        # 🆕 FIX 2: agora a categoria de receita "Extras" existe (criada nos seeds)
        if not cat_extras_desp:
            resultados["extras"].detalhes_erros.append(
                "Categoria despesa 'Extras' nao encontrada"
            )
        if not cat_extras_rec:
            resultados["extras"].detalhes_erros.append(
                "Categoria receita 'Extras' nao encontrada"
            )

        for i, linha in enumerate(linhas[:45]):
            if i < 30 or i > 40:
                continue
            for mes_num, col_idx in mapa_meses.items():
                if col_idx >= len(linha) or col_idx + 1 >= len(linha):
                    continue
                desc = linha[col_idx]
                valor = parse_numero(linha[col_idx + 1])
                if not desc or not isinstance(desc, str):
                    continue
                desc_str = str(desc).strip()
                if not desc_str or valor is None or valor == 0:
                    continue

                if valor > 0:
                    # RECEITA Extras
                    if not cat_extras_rec:
                        continue
                    if not dry_run:
                        rec = LancamentoReceita(
                            ano_id=ano_obj.id, mes=mes_num,
                            categoria_id=cat_extras_rec.id,
                            conta_id=conta_padrao.id,
                            valor=valor, descricao=desc_str,
                        )
                        db.add(rec)
                    resultados["extras"].inseridos += 1
                    resultados["extras"].detalhes_inseridos.append(
                        f"+ {desc_str} {ano_num}/{mes_num} = R$ {valor:.2f}"
                    )
                else:
                    # DESPESA Extras
                    if not cat_extras_desp:
                        continue
                    if not dry_run:
                        desp = LancamentoDespesa(
                            ano_id=ano_obj.id, mes=mes_num,
                            categoria_id=cat_extras_desp.id,
                            origem_tipo="conta", conta_id=conta_padrao.id,
                            valor=abs(valor), descricao=desc_str,
                        )
                        db.add(desp)
                    resultados["extras"].inseridos += 1
                    resultados["extras"].detalhes_inseridos.append(
                        f"- {desc_str} {ano_num}/{mes_num} = R$ {abs(valor):.2f}"
                    )

        if not dry_run:
            db.commit()
        resultados["extras"].mensagem = (
            f"{resultados['extras'].inseridos} extras inseridos"
        )

    # ============================================================
    # BLOCO 4: Combustivel (linhas 40-43)
    # ============================================================
    if "combustivel" in blocos:
        resultados["combustivel"] = ResultadoImportacao()
        PRECO_MEDIO_LITRO = 6.0

        for i, linha in enumerate(linhas[:48]):
            if i < 39 or i > 46:
                continue
            for mes_num, col_idx in mapa_meses.items():
                if col_idx >= len(linha) or col_idx + 1 >= len(linha):
                    continue
                dia = parse_numero(linha[col_idx])
                valor = parse_numero(linha[col_idx + 1])
                if dia is None or valor is None or dia <= 0 or valor <= 0:
                    continue
                dia_int = int(dia)
                if dia_int > 31:
                    continue

                try:
                    data_abast = date(ano_num, mes_num, dia_int)
                except ValueError:
                    continue

                litros_est = round(valor / PRECO_MEDIO_LITRO, 3)

                existe = db.scalar(select(LancamentoCombustivel).where(
                    LancamentoCombustivel.ano_id == ano_obj.id,
                    LancamentoCombustivel.mes == mes_num,
                    LancamentoCombustivel.data == data_abast,
                    LancamentoCombustivel.valor_total == valor,
                ))
                if existe:
                    resultados["combustivel"].pulados += 1
                    continue

                if not dry_run:
                    comb = LancamentoCombustivel(
                        ano_id=ano_obj.id, mes=mes_num,
                        data=data_abast,
                        litros=litros_est, valor_total=valor,
                        posto=None, veiculo=None,
                    )
                    db.add(comb)
                resultados["combustivel"].inseridos += 1

        if not dry_run:
            db.commit()
        resultados["combustivel"].mensagem = (
            f"{resultados['combustivel'].inseridos} abastecimentos inseridos"
        )

    # ============================================================
    # PAGAMENTOS DE CARTAO
    # ============================================================
    if "pagamentos_cartao" in blocos:
        resultados["pagamentos_cartao"] = ResultadoImportacao()

        cartao_itau = buscar_cartao(db, "Itau Cartao")
        conta_itau = buscar_conta(db, "Itau C/C")

        if not cartao_itau or not conta_itau:
            resultados["pagamentos_cartao"].detalhes_erros.append(
                "Cartao ou conta nao encontrados"
            )
        else:
            for i, linha in enumerate(linhas[:20]):
                if i < 3 or i > 16:
                    continue
                if len(linha) < 2:
                    continue
                nome_cat = linha[1]
                if not nome_cat or not isinstance(nome_cat, str):
                    continue
                nome_limpo = str(nome_cat).strip()
                if nome_limpo.startswith("("):
                    partes = nome_limpo.split(")", 1)
                    if len(partes) > 1:
                        nome_limpo = partes[1].strip()

                if nome_limpo not in ("Cartao", "Cartão"):
                    continue

                for mes_num, col_idx in mapa_meses.items():
                    if col_idx >= len(linha):
                        continue
                    valor_raw = parse_numero(linha[col_idx])
                    if valor_raw is None or valor_raw == 0:
                        continue
                    # 🆕 FIX: usa abs (planilha pode ter negativo)
                    valor = abs(valor_raw)

                    existe = db.scalar(select(PagamentoCartao).where(
                        PagamentoCartao.ano_id == ano_obj.id,
                        PagamentoCartao.mes == mes_num,
                        PagamentoCartao.cartao_id == cartao_itau.id,
                    ))
                    if existe:
                        resultados["pagamentos_cartao"].pulados += 1
                        continue

                    if not dry_run:
                        pag = PagamentoCartao(
                            ano_id=ano_obj.id, mes=mes_num,
                            cartao_id=cartao_itau.id,
                            conta_id=conta_itau.id,
                            valor=valor,
                            descricao=f"Importado da planilha {ano_num}/{mes_num}",
                        )
                        db.add(pag); db.flush()

                        cat_cartao = buscar_categoria_despesa(db, "Cartao")
                        if cat_cartao:
                            desp = LancamentoDespesa(
                                ano_id=ano_obj.id, mes=mes_num,
                                categoria_id=cat_cartao.id,
                                origem_tipo="conta", conta_id=conta_itau.id,
                                valor=valor,
                                descricao=f"Pagamento {cartao_itau.nome}",
                                recorrente=0, auto_pagamento_cartao=1,
                                pagamento_cartao_id=pag.id,
                            )
                            db.add(desp)

                    resultados["pagamentos_cartao"].inseridos += 1

        if not dry_run:
            db.commit()
        resultados["pagamentos_cartao"].mensagem = (
            f"{resultados['pagamentos_cartao'].inseridos} pagamentos inseridos"
        )

    # ============================================================
    # SALDOS DE INVESTIMENTOS
    # ============================================================
    if "saldos_investimentos" in blocos:
        resultados["saldos_investimentos"] = ResultadoImportacao()

        categoria_atual = None
        for i, linha in enumerate(linhas[:80]):
            if i < 50 or i > 75:
                continue
            if len(linha) < 2:
                continue

            for col_check in range(0, min(5, len(linha))):
                v = linha[col_check]
                if v and isinstance(v, str):
                    v_str = str(v).strip()
                    if v_str in ("Previdência", "Previdencia"):
                        categoria_atual = "previdencia"
                        break
                    elif v_str == "FGTS":
                        categoria_atual = "fgts"
                        break
                    elif v_str in ("Renda Variável", "Renda Variavel", "Cripto"):
                        categoria_atual = None
                        break

            nome_linha = linha[1] if len(linha) > 1 else None
            if not nome_linha or str(nome_linha).strip() != "Saldo":
                continue
            if not categoria_atual:
                continue

            produto = buscar_produto(db, categoria_atual)
            if not produto:
                continue

            for mes_num, col_idx in mapa_meses.items():
                if col_idx >= len(linha):
                    continue
                valor = parse_numero(linha[col_idx])
                if valor is None or valor <= 0:
                    continue

                existe = db.scalar(select(SaldoInvestimento).where(
                    SaldoInvestimento.ano_id == ano_obj.id,
                    SaldoInvestimento.mes == mes_num,
                    SaldoInvestimento.produto_id == produto.id,
                ))
                if existe:
                    resultados["saldos_investimentos"].pulados += 1
                    continue

                if not dry_run:
                    saldo = SaldoInvestimento(
                        ano_id=ano_obj.id, mes=mes_num,
                        produto_id=produto.id,
                        saldo=valor, saldo_brl=valor,
                    )
                    db.add(saldo)
                resultados["saldos_investimentos"].inseridos += 1

        if not dry_run:
            db.commit()
        resultados["saldos_investimentos"].mensagem = (
            f"{resultados['saldos_investimentos'].inseridos} saldos de inv. inseridos"
        )

    return resultados


def importar_movimentos_multi_anos(
    db: Session, wb: Workbook, anos: list, blocos: list, dry_run: bool = False
) -> dict:
    """Importa multiplos anos."""
    relatorio_geral = {}
    for ano in anos:
        logger.info(f"Importando ano {ano}...")
        try:
            res = importar_movimentos_ano(db, wb, ano, blocos, dry_run)
            relatorio_geral[str(ano)] = res
        except Exception as e:
            logger.error(f"Erro no ano {ano}: {e}")
            relatorio_geral[str(ano)] = {"erro": str(e)}
    return relatorio_geral