from datetime import datetime, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import Escopo, UsuarioContexto, get_current_user, get_escopo
from app.models import Hidrometro, Leitura
from app.schemas import ConsumoOut, ConsumoPontoOut
from app.services.acesso import unidade_acessivel

router = APIRouter(prefix="/api/unidades", tags=["consumo"])


def _inicio_bucket(ts: datetime, agrupar: str) -> datetime:
    if agrupar == "dia":
        return ts.replace(hour=0, minute=0, second=0, microsecond=0)
    return ts.replace(minute=0, second=0, microsecond=0)


@router.get("/{unidade_id}/consumo", response_model=ConsumoOut)
def consumo(
    unidade_id: int,
    de: datetime | None = None,
    ate: datetime | None = None,
    dias: int | None = Query(None, ge=1, le=366),
    agrupar: Literal["hora", "dia"] = "dia",
    user: UsuarioContexto = Depends(get_current_user),
    escopo: Escopo = Depends(get_escopo),
    db: Session = Depends(get_db),
):
    """Consumo em litros da unidade, agrupado por hora ou dia (RF09). O consumo
    de cada leitura é a diferença para a anterior. Sem `de`/`ate`, usa os
    últimos `dias` (padrão 30) contados a partir da leitura mais recente."""
    unidade = unidade_acessivel(db, user, escopo, unidade_id)
    if unidade is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unidade não encontrada.")
    if unidade is False:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Você não tem acesso a essa unidade.")

    hidrometro_ids = [h.id for h in db.query(Hidrometro.id).filter_by(unidade_id=unidade_id).all()]
    vazio = ConsumoOut(unidade_id=unidade_id, agrupar=agrupar, total_litros=0, pontos=[])
    if not hidrometro_ids:
        return vazio

    de = de.replace(tzinfo=None) if de else None
    ate = ate.replace(tzinfo=None) if ate else None
    if not ate:
        ate = db.query(func.max(Leitura.timestamp)).filter(Leitura.hidrometro_id.in_(hidrometro_ids)).scalar()
        if ate is None:
            return vazio
    if not de:
        de = ate - timedelta(days=dias or 30)
    if de > ate:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "'de' deve ser anterior a 'ate'.")
    # Alinha o início ao bucket para o primeiro ponto não ser parcial.
    de = _inicio_bucket(de, agrupar)

    buckets: dict[datetime, float] = {}
    for hid in hidrometro_ids:
        # A leitura imediatamente anterior a `de` serve de referência para o delta da primeira do período.
        referencia = (
            db.query(Leitura)
            .filter(Leitura.hidrometro_id == hid, Leitura.timestamp < de)
            .order_by(Leitura.timestamp.desc())
            .first()
        )
        leituras = (
            db.query(Leitura.timestamp, Leitura.litros_acumulados)
            .filter(Leitura.hidrometro_id == hid, Leitura.timestamp >= de, Leitura.timestamp <= ate)
            .order_by(Leitura.timestamp)
            .all()
        )
        anterior = referencia.litros_acumulados if referencia else None
        for ts, acumulado in leituras:
            if anterior is not None:
                chave = _inicio_bucket(ts, agrupar)
                buckets[chave] = buckets.get(chave, 0.0) + (acumulado - anterior)
            anterior = acumulado

    pontos = [ConsumoPontoOut(inicio=k, litros=round(v, 2)) for k, v in sorted(buckets.items())]
    return ConsumoOut(
        unidade_id=unidade_id,
        agrupar=agrupar,
        de=de,
        ate=ate,
        total_litros=round(sum(p.litros for p in pontos), 2),
        pontos=pontos,
    )
