from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.deps import Escopo, UsuarioContexto, get_current_user, get_escopo, require_role
from app.models import Bloco, Hidrometro, Unidade
from app.schemas import UnidadeCreate, UnidadeOut, UnidadeUpdate

router = APIRouter(prefix="/api/unidades", tags=["unidades"])


def _bloco_no_escopo(db: Session, escopo: Escopo, bloco_id: int) -> Bloco | None | bool:
    """None = não existe, False = existe mas fora do escopo, Bloco = ok."""
    bloco = db.get(Bloco, bloco_id)
    if not bloco:
        return None
    return bloco if bloco.condominio_id in escopo.condominio_ids else False


@router.get("", response_model=list[UnidadeOut])
def listar(
    user: UsuarioContexto = Depends(get_current_user),
    escopo: Escopo = Depends(get_escopo),
    db: Session = Depends(get_db),
):
    """Síndico vê as unidades dos blocos do(s) condomínio(s) que administra;
    morador vê apenas a(s) própria(s) unidade(s) (RF03/RF04/RF06)."""
    query = db.query(Unidade).options(joinedload(Unidade.bloco), joinedload(Unidade.hidrometros))
    if user.papel == "sindico":
        query = query.join(Bloco).filter(Bloco.condominio_id.in_(escopo.condominio_ids))
    else:
        query = query.filter(Unidade.id.in_(escopo.unidade_ids))
    return query.order_by(Unidade.numero).all()


@router.post("", status_code=status.HTTP_201_CREATED)
def criar(
    dados: UnidadeCreate,
    _user: UsuarioContexto = Depends(require_role("sindico")),
    escopo: Escopo = Depends(get_escopo),
    db: Session = Depends(get_db),
):
    """Aceita uma única unidade (`numero`) ou várias de uma vez (`numeros`).
    Cada unidade nasce com seu hidrômetro criado junto (1 hidrômetro por
    unidade nesta escala do projeto)."""
    lista_numeros = [str(n).strip() for n in (dados.numeros or []) if str(n).strip()]
    if not lista_numeros and dados.numero and dados.numero.strip():
        lista_numeros = [dados.numero.strip()]

    if not lista_numeros:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "blocoId e ao menos um número de unidade são obrigatórios.")

    bloco = _bloco_no_escopo(db, escopo, dados.bloco_id)
    if bloco is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Bloco não encontrado.")
    if bloco is False:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Você não administra esse bloco.")

    criadas: list[Unidade] = []
    for numero in lista_numeros:
        unidade = Unidade(numero=numero, bloco_id=dados.bloco_id)
        db.add(unidade)
        db.flush()  # gera unidade.id antes de criar o hidrômetro
        # numeroSerie deriva do id da unidade — garante unicidade sem o síndico precisar informar nada.
        db.add(Hidrometro(unidade_id=unidade.id, numero_serie=f"HID-{unidade.id}"))
        criadas.append(unidade)

    db.commit()
    for unidade in criadas:
        db.refresh(unidade)

    saida = [UnidadeOut.model_validate(u) for u in criadas]
    return saida[0] if len(saida) == 1 else saida


@router.put("/{unidade_id}", response_model=UnidadeOut)
def atualizar(
    unidade_id: int,
    dados: UnidadeUpdate,
    _user: UsuarioContexto = Depends(require_role("sindico")),
    escopo: Escopo = Depends(get_escopo),
    db: Session = Depends(get_db),
):
    unidade = db.get(Unidade, unidade_id)
    if not unidade:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unidade não encontrada.")
    bloco = _bloco_no_escopo(db, escopo, unidade.bloco_id)
    if not bloco:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Você não administra essa unidade.")

    unidade.numero = dados.numero
    db.commit()
    db.refresh(unidade)
    return unidade


@router.delete("/{unidade_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover(
    unidade_id: int,
    _user: UsuarioContexto = Depends(require_role("sindico")),
    escopo: Escopo = Depends(get_escopo),
    db: Session = Depends(get_db),
):
    unidade = db.get(Unidade, unidade_id)
    if not unidade:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unidade não encontrada.")
    bloco = _bloco_no_escopo(db, escopo, unidade.bloco_id)
    if not bloco:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Você não administra essa unidade.")

    db.delete(unidade)
    db.commit()
