"""Regras de negócio de leituras compartilhadas entre a API e o simulador."""

from datetime import datetime


def calcular_vazao(
    anterior_litros: float | None, anterior_ts: datetime | None, litros: float, ts: datetime
) -> float | None:
    """Vazão instantânea em L/h: (Δ litros acumulados) / (Δ horas). None se não
    houver leitura anterior."""
    if anterior_litros is None or anterior_ts is None:
        return None
    horas = (ts - anterior_ts).total_seconds() / 3600
    if horas <= 0:
        return None
    return (litros - anterior_litros) / horas
