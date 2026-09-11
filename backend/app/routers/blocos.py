from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import Escopo, UsuarioContexto, get_current_user, get_escopo, require_role
from app.models import Bloco, Unidade
from app.schemas import BlocoCreate, BlocoOut, BlocoUpdate

router = APIRouter(prefix="/api/blocos", tags=["blocos"])


@router.get("", response_model=list[BlocoOut])
def listar(
    user: UsuarioContexto = Depends(get_current_user),
    escopo: Escopo = Depends(get_escopo),
    db: Session = Depends(get_db),
):
    """Síndico vê os blocos do(s) condomínio(s) que administra; morador vê
    apenas o(s) bloco(s) da(s) própria(s) unidade(s) (RF03/RF04/RF06)."""
    if user.papel == "sindico":
        query = db.query(Bloco).filter(Bloco.condominio_id.in_(escopo.condominio_ids))
    else:
        query = db.query(Bloco).join(Unidade).filter(Unidade.id.in_(escopo.unidade_ids)).distinct()
    return query.order_by(Bloco.nome).all()


@router.post("", response_model=BlocoOut, status_code=status.HTTP_201_CREATED)
def criar(
    dados: BlocoCreate,
    _user: UsuarioContexto = Depends(require_role("sindico")),
    escopo: Escopo = Depends(get_escopo),
    db: Session = Depends(get_db),
):
    """Só síndico, e só no próprio condomínio (RF05)."""
    if dados.condominio_id not in escopo.condominio_ids:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Você não administra esse condomínio.")

    bloco = Bloco(nome=dados.nome, condominio_id=dados.condominio_id)
    db.add(bloco)
    db.commit()
    db.refresh(bloco)
    return bloco


@router.put("/{bloco_id}", response_model=BlocoOut)
def atualizar(
    bloco_id: int,
    dados: BlocoUpdate,
    _user: UsuarioContexto = Depends(require_role("sindico")),
    escopo: Escopo = Depends(get_escopo),
    db: Session = Depends(get_db),
):
    bloco = db.get(Bloco, bloco_id)
    if not bloco:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Bloco não encontrado.")
    if bloco.condominio_id not in escopo.condominio_ids:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Você não administra esse bloco.")

    bloco.nome = dados.nome
    db.commit()
    db.refresh(bloco)
    return bloco


@router.delete("/{bloco_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover(
    bloco_id: int,
    _user: UsuarioContexto = Depends(require_role("sindico")),
    escopo: Escopo = Depends(get_escopo),
    db: Session = Depends(get_db),
):
    bloco = db.get(Bloco, bloco_id)
    if not bloco:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Bloco não encontrado.")
    if bloco.condominio_id not in escopo.condominio_ids:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Você não administra esse bloco.")

    db.delete(bloco)
    db.commit()
