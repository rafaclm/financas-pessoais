from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.infrastructure.db.models import (
    CategoriaDespesa, CategoriaReceita, Instituicao, Ano
)


SEED_CATEGORIAS_DESPESA = [
    ("Escola", "fixa", 1, "#3B82F6"),
    ("Cartão", "variavel", 1, "#EF4444"),
    ("Net", "fixa", 1, "#06B6D4"),
    ("Combustível", "variavel", 1, "#F97316"),
    ("Financiamento", "fixa", 1, "#8B5CF6"),
    ("Extras", "variavel", 0, "#A78BFA"),
    ("Investimento", "variavel", 1, "#10B981"),
    ("Adiantamento", "variavel", 0, "#6B7280"),
    ("Aluguel", "fixa", 1, "#EC4899"),
]

SEED_CATEGORIAS_RECEITA = [
    ("Salário", "recorrente"),
    ("Adiantamento", "recorrente"),
    ("Bônus", "eventual"),
    ("13º", "eventual"),
    ("Férias", "eventual"),
    ("Restituição IR", "eventual"),
    ("Aluguel Recebido", "recorrente"),
    ("Outros", "eventual"),
]

SEED_INSTITUICOES = [
    ("Itaú", "banco", "BR"),
    ("Bradesco", "banco", "BR"),
    ("Nomad", "banco", "BR"),
    ("Avenue", "corretora", "US"),
    ("Mercado Livre", "banco", "BR"),
]


def run_seeds(db: Session) -> None:
    if not db.scalar(select(CategoriaDespesa).limit(1)):
        for nome, tipo, ess, cor in SEED_CATEGORIAS_DESPESA:
            db.add(CategoriaDespesa(nome=nome, tipo=tipo, essencial=ess, cor=cor))

    if not db.scalar(select(CategoriaReceita).limit(1)):
        for nome, rec in SEED_CATEGORIAS_RECEITA:
            db.add(CategoriaReceita(nome=nome, recorrencia=rec))

    if not db.scalar(select(Instituicao).limit(1)):
        for nome, tipo, pais in SEED_INSTITUICOES:
            db.add(Instituicao(nome=nome, tipo=tipo, pais=pais))

    # Cria o ano corrente automaticamente, se não existir
    ano_corrente = datetime.now().year
    if not db.scalar(select(Ano).where(Ano.ano == ano_corrente)):
        db.add(Ano(ano=ano_corrente, saldo_inicial=0, ativo=1,
                   observacao="Ano criado automaticamente"))

    db.commit()