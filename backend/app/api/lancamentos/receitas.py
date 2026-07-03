from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from app.api.deps import DbSession
from app.infrastructure.db.models import LancamentoReceita, Ano, CategoriaReceita, Conta
from app.schemas.receitas import ReceitaCreate, ReceitaUpdate, ReceitaOut

router = APIRouter(prefix="/receitas", tags=["Lancamentos - Receitas"])


def _validar_refs(db, payload):
    if not db.get(Ano, payload.ano_id):
        raise HTTPException(400, "Ano inválido")
    if not db.get(CategoriaReceita, payload.categoria_id):
        raise HTTPException(400, "Categoria inválida")
    if not db.get(Conta, payload.conta_id):
        raise HTTPException(400, "Conta inválida")


@router.get("", response_model=list[ReceitaOut])
def listar(
    db: DbSession,
    ano_id: int | None = None,
    mes: int | None = None,
    categoria_id: int | None = None,
    conta_id: int | None = None,
):
    stmt = select(LancamentoReceita).order_by(
        LancamentoReceita.ano_id.desc(),
        LancamentoReceita.mes.desc(),
        LancamentoReceita.id.desc(),
    )
    if ano_id:
        stmt = stmt.where(LancamentoReceita.ano_id == ano_id)
    if mes:
        stmt = stmt.where(LancamentoReceita.mes == mes)
    if categoria_id:
        stmt = stmt.where(LancamentoReceita.categoria_id == categoria_id)
    if conta_id:
        stmt = stmt.where(LancamentoReceita.conta_id == conta_id)
    return db.scalars(stmt).all()


@router.get("/{item_id}", response_model=ReceitaOut)
def obter(item_id: int, db: DbSession):
    obj = db.get(LancamentoReceita, item_id)
    if not obj:
        raise HTTPException(404, "Receita não encontrada")
    return obj


@router.post("", response_model=ReceitaOut, status_code=status.HTTP_201_CREATED)
def criar(payload: ReceitaCreate, db: DbSession):
    _validar_refs(db, payload)
    obj = LancamentoReceita(**payload.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj


@router.put("/{item_id}", response_model=ReceitaOut)
def atualizar(item_id: int, payload: ReceitaUpdate, db: DbSession):
    obj = db.get(LancamentoReceita, item_id)
    if not obj:
        raise HTTPException(404, "Receita não encontrada")
    data = payload.model_dump(exclude_unset=True)
    if "categoria_id" in data and not db.get(CategoriaReceita, data["categoria_id"]):
        raise HTTPException(400, "Categoria inválida")
    if "conta_id" in data and not db.get(Conta, data["conta_id"]):
        raise HTTPException(400, "Conta inválida")
    for k, v in data.items():
        setattr(obj, k, v)
    db.commit(); db.refresh(obj)
    return obj


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(item_id: int, db: DbSession):
    obj = db.get(LancamentoReceita, item_id)
    if not obj:
        raise HTTPException(404, "Receita não encontrada")
    db.delete(obj); db.commit()