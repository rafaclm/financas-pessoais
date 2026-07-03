from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select, func
from app.api.deps import DbSession
from app.infrastructure.db.models import LancamentoCombustivel, Ano, Conta, Cartao
from app.schemas.combustivel import (
    CombustivelCreate, CombustivelUpdate, CombustivelOut
)

router = APIRouter(prefix="/combustivel", tags=["Lancamentos - Combustivel"])


def _validar_refs(db, payload):
    if not db.get(Ano, payload.ano_id):
        raise HTTPException(400, "Ano inválido")
    if payload.conta_id and not db.get(Conta, payload.conta_id):
        raise HTTPException(400, "Conta inválida")
    if payload.cartao_id and not db.get(Cartao, payload.cartao_id):
        raise HTTPException(400, "Cartão inválido")


@router.get("", response_model=list[CombustivelOut])
def listar(db: DbSession, ano_id: int | None = None, mes: int | None = None):
    stmt = select(LancamentoCombustivel).order_by(
        LancamentoCombustivel.data.desc(),
        LancamentoCombustivel.id.desc(),
    )
    if ano_id: stmt = stmt.where(LancamentoCombustivel.ano_id == ano_id)
    if mes: stmt = stmt.where(LancamentoCombustivel.mes == mes)
    return db.scalars(stmt).all()


@router.get("/resumo")
def resumo(db: DbSession, ano_id: int):
    rows = db.execute(
        select(
            LancamentoCombustivel.mes,
            func.sum(LancamentoCombustivel.litros).label("total_litros"),
            func.sum(LancamentoCombustivel.valor_total).label("total_valor"),
            func.count(LancamentoCombustivel.id).label("qtd_abastecimentos"),
        )
        .where(LancamentoCombustivel.ano_id == ano_id)
        .group_by(LancamentoCombustivel.mes)
        .order_by(LancamentoCombustivel.mes)
    ).all()
    return [
        {
            "mes": r.mes,
            "total_litros": float(r.total_litros or 0),
            "total_valor": float(r.total_valor or 0),
            "preco_medio_litro": (
                round(float(r.total_valor) / float(r.total_litros), 4)
                if r.total_litros else 0
            ),
            "qtd_abastecimentos": r.qtd_abastecimentos,
        }
        for r in rows
    ]


@router.get("/{item_id}", response_model=CombustivelOut)
def obter(item_id: int, db: DbSession):
    obj = db.get(LancamentoCombustivel, item_id)
    if not obj:
        raise HTTPException(404, "Não encontrado")
    return obj


@router.post("", response_model=CombustivelOut, status_code=status.HTTP_201_CREATED)
def criar(payload: CombustivelCreate, db: DbSession):
    _validar_refs(db, payload)
    obj = LancamentoCombustivel(**payload.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj


@router.put("/{item_id}", response_model=CombustivelOut)
def atualizar(item_id: int, payload: CombustivelUpdate, db: DbSession):
    obj = db.get(LancamentoCombustivel, item_id)
    if not obj:
        raise HTTPException(404, "Não encontrado")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit(); db.refresh(obj)
    return obj


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(item_id: int, db: DbSession):
    obj = db.get(LancamentoCombustivel, item_id)
    if not obj:
        raise HTTPException(404, "Não encontrado")
    db.delete(obj); db.commit()