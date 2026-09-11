from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import UsuarioCondominio, UsuarioUnidade
from app.security import decodificar_token


@dataclass
class UsuarioContexto:
    id: int
    papel: str
    nome: str
    email: str


@dataclass
class Escopo:
    condominio_ids: list[int]
    unidade_ids: list[int]


def get_current_user(request: Request) -> UsuarioContexto:
    """Valida o JWT no header Authorization e devolve o usuário logado."""
    header = request.headers.get("authorization", "")
    partes = header.split(" ")
    if len(partes) != 2 or partes[0] != "Bearer":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token de autenticação ausente.")

    try:
        payload = decodificar_token(partes[1])
    except Exception:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido ou expirado.")

    return UsuarioContexto(
        id=int(payload["sub"]), papel=payload["papel"], nome=payload["nome"], email=payload["email"]
    )


def require_role(*papeis: str):
    """Bloqueia a rota se o papel do usuário logado não estiver entre os permitidos."""

    def dependency(user: UsuarioContexto = Depends(get_current_user)) -> UsuarioContexto:
        if user.papel not in papeis:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Acesso negado para este papel.")
        return user

    return dependency


def get_escopo(user: UsuarioContexto = Depends(get_current_user), db: Session = Depends(get_db)) -> Escopo:
    """Resolve o escopo de acesso do usuário logado (RF03/RF04): condomínios
    administrados (síndico) ou unidades vinculadas (morador)."""
    if user.papel == "sindico":
        condominio_ids = [
            v.condominio_id for v in db.query(UsuarioCondominio).filter_by(usuario_id=user.id).all()
        ]
        return Escopo(condominio_ids=condominio_ids, unidade_ids=[])

    unidade_ids = [v.unidade_id for v in db.query(UsuarioUnidade).filter_by(usuario_id=user.id).all()]
    return Escopo(condominio_ids=[], unidade_ids=unidade_ids)
