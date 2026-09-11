from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import Escopo, UsuarioContexto, get_current_user, get_escopo
from app.models import Bloco, Condominio, Unidade
from app.schemas import CondominioOut

router = APIRouter(prefix="/api/condominios", tags=["condominios"])


@router.get("", response_model=list[CondominioOut])
def listar(
    user: UsuarioContexto = Depends(get_current_user),
    escopo: Escopo = Depends(get_escopo),
    db: Session = Depends(get_db),
):
    """Somente leitura: síndico vê o(s) condomínio(s) que administra
    (necessário no frontend pra saber onde cadastrar o primeiro bloco).
    Morador vê o condomínio da própria unidade."""
    if user.papel == "sindico":
        query = db.query(Condominio).filter(Condominio.id.in_(escopo.condominio_ids))
    else:
        query = (
            db.query(Condominio)
            .join(Bloco, Bloco.condominio_id == Condominio.id)
            .join(Unidade, Unidade.bloco_id == Bloco.id)
            .filter(Unidade.id.in_(escopo.unidade_ids))
            .distinct()
        )
    return query.order_by(Condominio.nome).all()
