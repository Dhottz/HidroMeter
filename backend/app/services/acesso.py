"""Checagem de escopo (RF03/RF04) reaproveitada pelos endpoints de leituras."""

from sqlalchemy.orm import Session

from app.deps import Escopo, UsuarioContexto
from app.models import Hidrometro, Unidade


def unidade_acessivel(db: Session, user: UsuarioContexto, escopo: Escopo, unidade_id: int) -> Unidade | None | bool:
    """None = não existe, False = existe mas fora do escopo, Unidade = ok."""
    unidade = db.get(Unidade, unidade_id)
    if not unidade:
        return None
    if user.papel == "sindico":
        permitido = unidade.bloco.condominio_id in escopo.condominio_ids
    else:
        permitido = unidade.id in escopo.unidade_ids
    return unidade if permitido else False


def hidrometro_acessivel(
    db: Session, user: UsuarioContexto, escopo: Escopo, hidrometro_id: int
) -> Hidrometro | None | bool:
    """None = não existe, False = existe mas fora do escopo, Hidrometro = ok."""
    hidrometro = db.get(Hidrometro, hidrometro_id)
    if not hidrometro:
        return None
    return hidrometro if unidade_acessivel(db, user, escopo, hidrometro.unidade_id) else False
