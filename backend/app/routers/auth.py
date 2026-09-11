from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Condominio, Papel, Unidade, Usuario, UsuarioCondominio, UsuarioUnidade
from app.schemas import LoginIn, RegisterIn, TokenOut
from app.security import criar_token, hash_senha, verificar_senha

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register(dados: RegisterIn, db: Session = Depends(get_db)):
    """Cria um usuário (síndico ou morador) e já vincula ao condomínio/unidade
    informado, via as tabelas de junção N:N."""
    if dados.papel == Papel.sindico and not dados.condominio_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "condominioId é obrigatório para papel 'sindico'.")
    if dados.papel == Papel.morador and not dados.unidade_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "unidadeId é obrigatório para papel 'morador'.")

    if db.query(Usuario).filter_by(email=dados.email).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Já existe um usuário com esse email.")

    if dados.papel == Papel.sindico:
        if not db.get(Condominio, dados.condominio_id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Condomínio não encontrado.")
    else:
        if not db.get(Unidade, dados.unidade_id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Unidade não encontrada.")

    usuario = Usuario(
        nome=dados.nome, email=dados.email, senha_hash=hash_senha(dados.senha), papel=dados.papel
    )
    db.add(usuario)
    db.flush()  # gera usuario.id antes de criar o vínculo

    if dados.papel == Papel.sindico:
        db.add(UsuarioCondominio(usuario_id=usuario.id, condominio_id=dados.condominio_id))
    else:
        db.add(UsuarioUnidade(usuario_id=usuario.id, unidade_id=dados.unidade_id))

    db.commit()
    db.refresh(usuario)
    return TokenOut(token=criar_token(usuario), usuario=usuario)


@router.post("/login", response_model=TokenOut)
def login(dados: LoginIn, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter_by(email=dados.email).first()
    if not usuario or not verificar_senha(dados.senha, usuario.senha_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Credenciais inválidas.")

    return TokenOut(token=criar_token(usuario), usuario=usuario)
