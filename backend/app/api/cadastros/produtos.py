from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from app.api.deps import DbSession
from app.infrastructure.db.models import ProdutoInvestimento, Instituicao
from app.schemas.produtos import ProdutoCreate, ProdutoUpdate, ProdutoOut

router = APIRouter(prefix="/produtos-investimento", tags=["Cadastros - Produtos"])


@router.get("", response_model=list[ProdutoOut])
def listar(db: DbSession, apenas_ativos: bool = False):
    stmt = select(ProdutoInvestimento).order_by(ProdutoInvestimento.nome)
    if apenas_ativos:
        stmt = stmt.where(ProdutoInvestimento.ativo == 1)
    return db.scalars(stmt).all()


@router.post("", response_model=ProdutoOut, status_code=status.HTTP_201_CREATED)
def criar(payload: ProdutoCreate, db: DbSession):
    if not db.get(Instituicao, payload.instituicao_id):
        raise HTTPException(400, "Instituição inválida")
    obj = ProdutoInvestimento(**payload.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj


@router.put("/{item_id}", response_model=ProdutoOut)
def atualizar(item_id: int, payload: ProdutoUpdate, db: DbSession):
    obj = db.get(ProdutoInvestimento, item_id)
    if not obj:
        raise HTTPException(404, "Não encontrado")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit(); db.refresh(obj)
    return obj


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def inativar(item_id: int, db: DbSession):
    obj = db.get(ProdutoInvestimento, item_id)
    if not obj:
        raise HTTPException(404, "Não encontrado")
    obj.ativo = 0; db.commit()