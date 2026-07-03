"""
Garante que as dependencias (categorias e contas) existem antes
da importacao das movimentacoes.
"""
from sqlalchemy.orm import Session
from sqlalchemy import select
from loguru import logger
from app.infrastructure.db.models import (
    CategoriaDespesa, CategoriaReceita, Conta, Instituicao, Cartao,
    ProdutoInvestimento
)


# Categorias necessarias para a importacao
CATEGORIAS_RECEITA_NECESSARIAS = [
    ("Adiantamento", "recorrente", "#10B981"),
    ("Salario", "recorrente", "#22C55E"),
    ("Bonus", "eventual", "#F59E0B"),
    ("13o", "eventual", "#84CC16"),
    # 🆕 FIX 1: Categoria "Extras" de RECEITA (estava faltando!)
    ("Extras", "eventual", "#A78BFA"),
]

CATEGORIAS_DESPESA_NECESSARIAS = [
    ("Investimento", "variavel", 1, "#10B981"),
    ("Combustivel", "variavel", 1, "#F97316"),
    ("Extras", "variavel", 0, "#A78BFA"),
    ("Escola", "fixa", 1, "#3B82F6"),
    ("Financiamento", "fixa", 1, "#8B5CF6"),
    ("Net", "fixa", 1, "#06B6D4"),
    ("Cartao", "variavel", 1, "#EF4444"),
]


def garantir_categorias(db: Session) -> dict:
    """Cria categorias necessarias se nao existirem."""
    resultado = {"receitas_criadas": [], "despesas_criadas": []}

    for nome, recorr, cor in CATEGORIAS_RECEITA_NECESSARIAS:
        existe = db.scalar(
            select(CategoriaReceita).where(CategoriaReceita.nome.in_([
                nome,
                nome.replace("Salario", "Salário"),
                nome.replace("Bonus", "Bônus"),
                nome.replace("13o", "13º"),
            ]))
        )
        if not existe:
            obj = CategoriaReceita(nome=nome, recorrencia=recorr, cor=cor)
            db.add(obj)
            resultado["receitas_criadas"].append(nome)

    for nome, tipo, ess, cor in CATEGORIAS_DESPESA_NECESSARIAS:
        existe = db.scalar(
            select(CategoriaDespesa).where(CategoriaDespesa.nome.in_([
                nome,
                nome.replace("Combustivel", "Combustível"),
                nome.replace("Cartao", "Cartão"),
            ]))
        )
        if not existe:
            obj = CategoriaDespesa(
                nome=nome, tipo=tipo, essencial=ess, cor=cor
            )
            db.add(obj)
            resultado["despesas_criadas"].append(nome)

    db.commit()
    logger.info(f"Categorias: {resultado}")
    return resultado


def buscar_categoria_receita(db: Session, nome: str) -> CategoriaReceita | None:
    """Busca categoria de receita por nome (case-insensitive, com variantes)."""
    variantes = [nome, nome.lower(), nome.upper()]
    mapa = {
        "Salário": "Salario", "Salario": "Salário",
        "Bônus": "Bonus", "Bonus": "Bônus",
        "13º": "13o", "13o": "13º",
        "Adiantamento": "Adiantamento",
        "Extras": "Extras",
    }
    if nome in mapa:
        variantes.append(mapa[nome])

    for v in variantes:
        cat = db.scalar(select(CategoriaReceita).where(CategoriaReceita.nome == v))
        if cat:
            return cat
    return None


def buscar_categoria_despesa(db: Session, nome: str) -> CategoriaDespesa | None:
    """Busca categoria de despesa por nome (com variantes)."""
    variantes = [nome, nome.lower(), nome.upper()]
    mapa = {
        "Combustível": "Combustivel", "Combustivel": "Combustível",
        "Cartão": "Cartao", "Cartao": "Cartão",
        "Extras": "Extras",
    }
    if nome in mapa:
        variantes.append(mapa[nome])

    for v in variantes:
        cat = db.scalar(select(CategoriaDespesa).where(CategoriaDespesa.nome == v))
        if cat:
            return cat
    return None


def garantir_instituicao(db: Session, nome: str, tipo: str = "banco", pais: str = "BR") -> Instituicao:
    """Cria instituicao se nao existir."""
    inst = db.scalar(select(Instituicao).where(Instituicao.nome == nome))
    if not inst:
        inst = Instituicao(nome=nome, tipo=tipo, pais=pais)
        db.add(inst)
        db.commit()
        db.refresh(inst)
    return inst


def garantir_contas_basicas(db: Session) -> dict:
    """Cria as contas basicas usadas na importacao."""
    resultado = {"contas_criadas": []}

    contas_padrao = [
        ("Itau C/C", "Itau", "banco", "BR", "corrente", "BRL"),
        ("Itau Inv", "Itau", "banco", "BR", "investimento", "BRL"),
        ("Bradesco C/C", "Bradesco", "banco", "BR", "corrente", "BRL"),
        ("Nomad", "Nomad", "banco", "BR", "internacional", "BRL"),
        ("Avenue", "Avenue", "corretora", "US", "internacional", "BRL"),
        ("Mercado Livre", "Mercado Livre", "banco", "BR", "corrente", "BRL"),
    ]

    for nome_conta, nome_inst, tipo_inst, pais, tipo_conta, moeda in contas_padrao:
        existe = db.scalar(select(Conta).where(Conta.nome == nome_conta))
        if not existe:
            inst = garantir_instituicao(db, nome_inst, tipo_inst, pais)
            obj = Conta(
                nome=nome_conta, instituicao_id=inst.id,
                tipo=tipo_conta, moeda=moeda
            )
            db.add(obj)
            resultado["contas_criadas"].append(nome_conta)

    db.commit()
    logger.info(f"Contas: {resultado}")
    return resultado


def garantir_cartoes_basicos(db: Session) -> dict:
    """Cria os cartoes basicos usados na importacao."""
    resultado = {"cartoes_criados": []}

    cartoes_padrao = [
        ("Itau Cartao", "Itau", "Itau C/C"),
        ("Bradesco Cartao", "Bradesco", "Bradesco C/C"),
    ]

    for nome_cart, nome_inst, nome_conta_pag in cartoes_padrao:
        existe = db.scalar(select(Cartao).where(Cartao.nome == nome_cart))
        if not existe:
            inst = garantir_instituicao(db, nome_inst)
            conta_pag = db.scalar(select(Conta).where(Conta.nome == nome_conta_pag))
            obj = Cartao(
                nome=nome_cart, instituicao_id=inst.id,
                conta_pagamento_id=conta_pag.id if conta_pag else None,
                dia_fechamento=15, dia_vencimento=25
            )
            db.add(obj)
            resultado["cartoes_criados"].append(nome_cart)

    db.commit()
    logger.info(f"Cartoes: {resultado}")
    return resultado


def garantir_produtos_investimento(db: Session) -> dict:
    """Cria produtos de investimento (Previdencia, FGTS)."""
    resultado = {"produtos_criados": []}

    inst = garantir_instituicao(db, "Itau")
    inst_fgts = garantir_instituicao(db, "Caixa", "banco", "BR")

    produtos_padrao = [
        ("Previdencia Privada", "previdencia", inst.id, "BRL"),
        ("FGTS", "fgts", inst_fgts.id, "BRL"),
    ]

    for nome, cat, inst_id, moeda in produtos_padrao:
        existe = db.scalar(select(ProdutoInvestimento).where(
            ProdutoInvestimento.nome == nome
        ))
        if not existe:
            obj = ProdutoInvestimento(
                nome=nome, categoria=cat,
                instituicao_id=inst_id, moeda=moeda
            )
            db.add(obj)
            resultado["produtos_criados"].append(nome)

    db.commit()
    logger.info(f"Produtos: {resultado}")
    return resultado


def buscar_conta(db: Session, nome: str) -> Conta | None:
    """Busca conta por nome (com variantes acentuadas)."""
    variantes = [nome]
    mapa = {
        "Itau C/C": "Itaú C/C", "Itaú C/C": "Itau C/C",
        "Itau Inv": "Itaú Inv", "Itaú Inv": "Itau Inv",
        "Outros (ML, etc.)": "Mercado Livre",
        "Outros (ML, etc)": "Mercado Livre",
        "Outros": "Mercado Livre",
    }
    if nome in mapa:
        variantes.append(mapa[nome])

    for v in variantes:
        c = db.scalar(select(Conta).where(Conta.nome == v))
        if c:
            return c
    return None


def buscar_cartao(db: Session, nome: str) -> Cartao | None:
    """Busca cartao por nome."""
    variantes = [nome]
    mapa = {
        "Itau Cartao": "Itaú Cartão", "Itaú Cartão": "Itau Cartao",
        "Bradesco Cartao": "Bradesco Cartão",
        "Bradesco Cartão": "Bradesco Cartao",
    }
    if nome in mapa:
        variantes.append(mapa[nome])

    for v in variantes:
        c = db.scalar(select(Cartao).where(Cartao.nome == v))
        if c:
            return c
    return None


def buscar_produto(db: Session, nome_busca: str) -> ProdutoInvestimento | None:
    """Busca produto por palavra-chave (Previdencia, FGTS)."""
    nome_lower = nome_busca.lower()
    todos = db.scalars(select(ProdutoInvestimento)).all()
    for p in todos:
        if nome_lower in p.nome.lower():
            return p
    return None