from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from app.api.deps import DbSession
from app.infrastructure.db.models import (
    PagamentoCartao, LancamentoDespesa, CategoriaDespesa,
    Ano, Cartao, Conta
)
from app.schemas.pagamentos_cartao import (
    PagamentoCartaoCreate, PagamentoCartaoUpdate, PagamentoCartaoOut
)

router = APIRouter(prefix="/pagamentos-cartao", tags=["Lancamentos - Pagamento Cartao"])


def _obter_categoria_cartao(db):
    """Localiza a categoria 'Cartao' (ou variações) que serve para vincular as despesas."""
    cat = db.scalar(
        select(CategoriaDespesa).where(
            CategoriaDespesa.nome.in_(["Cartão", "Cartao", "CARTÃO", "CARTAO"])
        )
    )
    if not cat:
        # Cria automaticamente caso não exista
        cat = CategoriaDespesa(
            nome="Cartão", tipo="variavel",
            essencial=1, cor="#EF4444"
        )
        db.add(cat); db.commit(); db.refresh(cat)
    return cat


def _validar_refs(db, payload):
    if not db.get(Ano, payload.ano_id):
        raise HTTPException(400, "Ano inválido")
    if not db.get(Cartao, payload.cartao_id):
        raise HTTPException(400, "Cartão inválido")
    if not db.get(Conta, payload.conta_id):
        raise HTTPException(400, "Conta inválida")


@router.get("", response_model=list[PagamentoCartaoOut])
def listar(
    db: DbSession,
    ano_id: int | None = None,
    mes: int | None = None,
    cartao_id: int | None = None,
):
    stmt = select(PagamentoCartao).order_by(
        PagamentoCartao.ano_id.desc(),
        PagamentoCartao.mes.desc(),
        PagamentoCartao.id.desc(),
    )
    if ano_id: stmt = stmt.where(PagamentoCartao.ano_id == ano_id)
    if mes: stmt = stmt.where(PagamentoCartao.mes == mes)
    if cartao_id: stmt = stmt.where(PagamentoCartao.cartao_id == cartao_id)
    return db.scalars(stmt).all()


@router.get("/{item_id}", response_model=PagamentoCartaoOut)
def obter(item_id: int, db: DbSession):
    obj = db.get(PagamentoCartao, item_id)
    if not obj:
        raise HTTPException(404, "Não encontrado")
    return obj


@router.post("", response_model=PagamentoCartaoOut, status_code=status.HTTP_201_CREATED)
def criar(payload: PagamentoCartaoCreate, db: DbSession):
    _validar_refs(db, payload)
    # Verifica duplicidade
    existe = db.scalar(
        select(PagamentoCartao).where(
            PagamentoCartao.ano_id == payload.ano_id,
            PagamentoCartao.mes == payload.mes,
            PagamentoCartao.cartao_id == payload.cartao_id,
        )
    )
    if existe:
        raise HTTPException(409, "Já existe pagamento para este cartão neste período")

    # Cria o pagamento
    obj = PagamentoCartao(**payload.model_dump())
    db.add(obj); db.flush()  # flush para ter o id

    # Cria a despesa automática vinculada
    cat_cartao = _obter_categoria_cartao(db)
    cartao = db.get(Cartao, payload.cartao_id)
    despesa = LancamentoDespesa(
        ano_id=payload.ano_id,
        mes=payload.mes,
        categoria_id=cat_cartao.id,
        origem_tipo="conta",
        conta_id=payload.conta_id,
        valor=payload.valor,
        descricao=f"Pagamento {cartao.nome}",
        recorrente=0,
        auto_pagamento_cartao=1,
        pagamento_cartao_id=obj.id,
    )
    db.add(despesa)
    db.commit(); db.refresh(obj)
    return obj


@router.put("/{item_id}", response_model=PagamentoCartaoOut)
def atualizar(item_id: int, payload: PagamentoCartaoUpdate, db: DbSession):
    obj = db.get(PagamentoCartao, item_id)
    if not obj:
        raise HTTPException(404, "Não encontrado")

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(obj, k, v)

    # Atualiza a despesa vinculada
    despesa = db.scalar(
        select(LancamentoDespesa).where(
            LancamentoDespesa.pagamento_cartao_id == obj.id
        )
    )
    if despesa:
        despesa.ano_id = obj.ano_id
        despesa.mes = obj.mes
        despesa.conta_id = obj.conta_id
        despesa.valor = obj.valor

    db.commit(); db.refresh(obj)
    return obj


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(item_id: int, db: DbSession):
    obj = db.get(PagamentoCartao, item_id)
    if not obj:
        raise HTTPException(404, "Não encontrado")

    # Remove despesa vinculada
    despesa = db.scalar(
        select(LancamentoDespesa).where(
            LancamentoDespesa.pagamento_cartao_id == obj.id
        )
    )
    if despesa:
        db.delete(despesa)
    db.delete(obj); db.commit()