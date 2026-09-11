from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.config import settings
from app.models import Usuario

ALGORITHM = "HS256"


def hash_senha(senha: str) -> str:
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verificar_senha(senha: str, senha_hash: str) -> bool:
    return bcrypt.checkpw(senha.encode("utf-8"), senha_hash.encode("utf-8"))


def criar_token(usuario: Usuario) -> str:
    agora = datetime.now(timezone.utc)
    payload = {
        "sub": str(usuario.id),
        "papel": usuario.papel.value,
        "nome": usuario.nome,
        "email": usuario.email,
        "iat": agora,
        "exp": agora + timedelta(seconds=settings.jwt_expires_seconds),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decodificar_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
