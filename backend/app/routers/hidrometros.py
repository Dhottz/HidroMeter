from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import Escopo, UsuarioContexto, get_current_user, get_escopo, require_role
from app.models import Bloco, Hidrometro, Unidade
from app.schemas import HidrometroCreate, HidrometroOut, HidrometroUpdate

router = APIRouter(prefix="/api/hidrometros", tags=["hidrometros"])


def _unidade_no_escopo(db: Session, escopo: Escopo, unidade_id: int) -> Unidade | None | bool:
    """None = não existe, False = existe mas fora do escopo, Unidade = ok."""
    unidade = db.get(Unidade, unidade_id)
    if not unidade:
        return None
    return unidade if unidade.bloco.condominio_id in escopo.condominio_ids else False


@router.get("", response_model=list[HidrometroOut])
def listar(
    user: UsuarioContexto = Depends(get_current_user),
    escopo: Escopo = Depends(get_escopo),
    db: Session = Depends(get_db),
):
    """Síndico vê os hidrômetros das unidades do(s) condomínio(s) que
    administra; morador vê apenas os da(s) própria(s) unidade(s) (RF03/RF04/RF06)."""
    query = db.query(Hidrometro)
    if user.papel == "sindico":
        query = (
            query.join(Unidade, Hidrometro.unidade_id == Unidade.id)
            .join(Bloco, Unidade.bloco_id == Bloco.id)
            .filter(Bloco.condominio_id.in_(escopo.condominio_ids))
        )
    else:
        query = query.filter(Hidrometro.unidade_id.in_(escopo.unidade_ids))
    return query.order_by(Hidrometro.id).all()


@router.post("", response_model=HidrometroOut, status_code=status.HTTP_201_CREATED)
def criar(
    dados: HidrometroCreate,
    _user: UsuarioContexto = Depends(require_role("sindico")),
    escopo: Escopo = Depends(get_escopo),
    db: Session = Depends(get_db),
):
    unidade = _unidade_no_escopo(db, escopo, dados.unidade_id)
    if unidade is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unidade não encontrada.")
    if unidade is False:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Você não administra essa unidade.")

    if db.query(Hidrometro).filter_by(numero_serie=dados.numero_serie).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Já existe um hidrômetro com esse número de série.")

    hidrometro = Hidrometro(
        unidade_id=dados.unidade_id,
        numero_serie=dados.numero_serie,
        litros_por_pulso=dados.litros_por_pulso if dados.litros_por_pulso is not None else 1,
    )
    db.add(hidrometro)
    db.commit()
    db.refresh(hidrometro)
    return hidrometro


@router.put("/{hidrometro_id}", response_model=HidrometroOut)
def atualizar(
    hidrometro_id: int,
    dados: HidrometroUpdate,
    _user: UsuarioContexto = Depends(require_role("sindico")),
    escopo: Escopo = Depends(get_escopo),
    db: Session = Depends(get_db),
):
    hidrometro = db.get(Hidrometro, hidrometro_id)
    if not hidrometro:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Hidrômetro não encontrado.")
    unidade = _unidade_no_escopo(db, escopo, hidrometro.unidade_id)
    if not unidade:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Você não administra esse hidrômetro.")

    if dados.numero_serie is not None:
        hidrometro.numero_serie = dados.numero_serie
    if dados.litros_por_pulso is not None:
        hidrometro.litros_por_pulso = dados.litros_por_pulso
    db.commit()
    db.refresh(hidrometro)
    return hidrometro


@router.delete("/{hidrometro_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover(
    hidrometro_id: int,
    _user: UsuarioContexto = Depends(require_role("sindico")),
    escopo: Escopo = Depends(get_escopo),
    db: Session = Depends(get_db),
):
    hidrometro = db.get(Hidrometro, hidrometro_id)
    if not hidrometro:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Hidrômetro não encontrado.")
    unidade = _unidade_no_escopo(db, escopo, hidrometro.unidade_id)
    if not unidade:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Você não administra esse hidrômetro.")

    db.delete(hidrometro)
    db.commit()
