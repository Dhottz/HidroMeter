from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import Escopo, UsuarioContexto, get_current_user, get_escopo, require_role
from app.models import Leitura
from app.schemas import LeituraIn, LeituraLoteIn, LeituraOut, LeituraPaginaOut
from app.services.acesso import hidrometro_acessivel
from app.services.leituras import calcular_vazao

router = APIRouter(prefix="/api/leituras", tags=["leituras"])


def _ultima_leitura(db: Session, hidrometro_id: int) -> Leitura | None:
    return db.query(Leitura).filter_by(hidrometro_id=hidrometro_id).order_by(Leitura.timestamp.desc()).first()


def _exigir_hidrometro(db: Session, user: UsuarioContexto, escopo: Escopo, hidrometro_id: int) -> None:
    hidrometro = hidrometro_acessivel(db, user, escopo, hidrometro_id)
    if hidrometro is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Hidrômetro {hidrometro_id} não encontrado.")
    if hidrometro is False:
        raise HTTPException(status.HTTP_403_FORBIDDEN, f"Você não administra o hidrômetro {hidrometro_id}.")


def _ingerir(db: Session, entradas: list[LeituraIn]) -> list[Leitura]:
    """Valida a sequência de cada hidrômetro e deriva a vazão (RF07/RF08).
    Regras: o timestamp tem que ser posterior à última leitura do hidrômetro e
    o contador acumulado não pode diminuir (é um odômetro)."""
    por_hidrometro: dict[int, list[LeituraIn]] = {}
    for e in entradas:
        por_hidrometro.setdefault(e.hidrometro_id, []).append(e)

    criadas: list[Leitura] = []
    for hid, itens in por_hidrometro.items():
        itens.sort(key=lambda e: e.timestamp)
        anterior = _ultima_leitura(db, hid)
        ant_litros = anterior.litros_acumulados if anterior else None
        ant_ts = anterior.timestamp if anterior else None

        for e in itens:
            if ant_ts is not None and e.timestamp <= ant_ts:
                raise HTTPException(
                    status.HTTP_409_CONFLICT,
                    f"Hidrômetro {hid}: leitura de {e.timestamp.isoformat()} não é posterior à última ({ant_ts.isoformat()}).",
                )
            if ant_litros is not None and e.litros_acumulados < ant_litros:
                raise HTTPException(
                    status.HTTP_409_CONFLICT,
                    f"Hidrômetro {hid}: litros acumulados ({e.litros_acumulados}) menores que a leitura anterior ({ant_litros}).",
                )
            leitura = Leitura(
                hidrometro_id=hid,
                timestamp=e.timestamp,
                litros_acumulados=e.litros_acumulados,
                vazao_instantanea=calcular_vazao(ant_litros, ant_ts, e.litros_acumulados, e.timestamp),
            )
            db.add(leitura)
            criadas.append(leitura)
            ant_litros, ant_ts = e.litros_acumulados, e.timestamp
    return criadas


@router.post("", response_model=LeituraOut, status_code=status.HTTP_201_CREATED)
def criar(
    dados: LeituraIn,
    user: UsuarioContexto = Depends(require_role("sindico")),
    escopo: Escopo = Depends(get_escopo),
    db: Session = Depends(get_db),
):
    _exigir_hidrometro(db, user, escopo, dados.hidrometro_id)
    leitura = _ingerir(db, [dados])[0]
    db.commit()
    db.refresh(leitura)
    return leitura


@router.post("/lote", status_code=status.HTTP_201_CREATED)
def criar_lote(
    dados: LeituraLoteIn,
    user: UsuarioContexto = Depends(require_role("sindico")),
    escopo: Escopo = Depends(get_escopo),
    db: Session = Depends(get_db),
):
    """Ingestão em lote (tudo ou nada): se qualquer leitura for inválida nada é gravado."""
    for hid in {e.hidrometro_id for e in dados.leituras}:
        _exigir_hidrometro(db, user, escopo, hid)
    criadas = _ingerir(db, dados.leituras)
    db.commit()
    return {"criadas": len(criadas)}


@router.get("", response_model=LeituraPaginaOut)
def listar(
    hidrometro_id: int = Query(alias="hidrometroId"),
    de: datetime | None = None,
    ate: datetime | None = None,
    limite: int = Query(100, ge=1, le=1000),
    deslocamento: int = Query(0, ge=0),
    user: UsuarioContexto = Depends(get_current_user),
    escopo: Escopo = Depends(get_escopo),
    db: Session = Depends(get_db),
):
    """Leituras brutas de um hidrômetro, paginadas (RNF05), da mais recente para a mais antiga."""
    _exigir_hidrometro(db, user, escopo, hidrometro_id)
    query = db.query(Leitura).filter(Leitura.hidrometro_id == hidrometro_id)
    if de:
        query = query.filter(Leitura.timestamp >= de.replace(tzinfo=None))
    if ate:
        query = query.filter(Leitura.timestamp <= ate.replace(tzinfo=None))
    total = query.with_entities(func.count(Leitura.id)).scalar()
    itens = query.order_by(Leitura.timestamp.desc()).offset(deslocamento).limit(limite).all()
    return LeituraPaginaOut(total=total, limite=limite, deslocamento=deslocamento, itens=itens)
