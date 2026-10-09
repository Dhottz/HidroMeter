"""Simulador de leituras de hidrômetros (Entrega 2, RNF04).

Gera de uma vez o histórico completo: garante ~50 unidades (cada uma com
hidrômetro) em cada bloco do primeiro condomínio, e grava N dias de leituras
horárias com padrão realista (picos de manhã e à noite, quase zero de
madrugada). 10 unidades recebem um vazamento injetado: vazão constante,
inclusive na janela noturna. Mesma seed + mesmo --fim => mesmo dataset.

Uso (a partir da pasta backend, com o venv ativo e o banco migrado):
    python ../simulator/simulate.py [--dias 90] [--seed 42] [--fim 2026-10-01]
"""

import argparse
import json
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND))

from sqlalchemy import insert  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.models import Bloco, Condominio, Hidrometro, Leitura, Unidade  # noqa: E402
from app.services.leituras import calcular_vazao  # noqa: E402

UNIDADES_POR_BLOCO = 50
UNIDADES_COM_VAZAMENTO = 10
LITROS_POR_PESSOA_DIA = 150

# Fração do consumo diário em cada hora (soma 1.0): madrugada quase zero,
# pico de manhã (6-9h), almoço, pico da noite (18-22h).
PERFIL_HORARIO = [
    0.002, 0.001, 0.001, 0.001, 0.003, 0.015,
    0.060, 0.100, 0.090, 0.050, 0.035, 0.045,
    0.060, 0.045, 0.030, 0.030, 0.035, 0.055,
    0.095, 0.110, 0.095, 0.060, 0.025, 0.007,
]
PERFIL_HORARIO = [p / sum(PERFIL_HORARIO) for p in PERFIL_HORARIO]


def garantir_estrutura(db) -> list[Hidrometro]:
    """Completa cada bloco do primeiro condomínio até UNIDADES_POR_BLOCO unidades,
    todas com hidrômetro, e devolve os hidrômetros em ordem estável."""
    condominio = db.query(Condominio).order_by(Condominio.id).first()
    if not condominio:
        sys.exit("Nenhum condomínio encontrado. Rode `python seed.py` no backend antes.")

    series_usadas = {s for (s,) in db.query(Hidrometro.numero_serie).all()}
    blocos = db.query(Bloco).filter_by(condominio_id=condominio.id).order_by(Bloco.id).all()
    for bloco in blocos:
        existentes = {u.numero for u in db.query(Unidade).filter_by(bloco_id=bloco.id).all()}
        letra = bloco.nome.strip()[-1].upper()
        i = 1
        while len(existentes) < UNIDADES_POR_BLOCO:
            numero = f"{letra}{i:02d}"
            i += 1
            if numero in existentes:
                continue
            db.add(Unidade(numero=numero, bloco_id=bloco.id))
            existentes.add(numero)
    db.flush()

    unidades = (
        db.query(Unidade).join(Bloco).filter(Bloco.condominio_id == condominio.id).order_by(Unidade.id).all()
    )
    for unidade in unidades:
        if not unidade.hidrometros:
            serie = f"HID-{unidade.numero}"
            if serie in series_usadas:
                serie = f"HID-{unidade.id}"
            series_usadas.add(serie)
            db.add(Hidrometro(unidade_id=unidade.id, numero_serie=serie, litros_por_pulso=1))
    db.commit()

    return [h for u in unidades for h in db.query(Hidrometro).filter_by(unidade_id=u.id).order_by(Hidrometro.id)]


def simular_hidrometro(rng: random.Random, inicio: datetime, horas: int, vazamento: dict | None):
    """Gera [(timestamp, litros_acumulados)] — contador em pulsos inteiros de 1 L."""
    moradores = rng.choice([1, 2, 2, 3, 3, 4, 5])
    consumo_dia = moradores * LITROS_POR_PESSOA_DIA * rng.uniform(0.7, 1.3)
    acumulado = float(rng.randint(5_000, 60_000))  # odômetro já em uso quando a série começa

    saida = []
    for h in range(horas):
        ts = inicio + timedelta(hours=h)
        fator_fds = 1.15 if ts.weekday() >= 5 else 1.0
        esperado = consumo_dia * PERFIL_HORARIO[ts.hour] * fator_fds
        litros = max(0.0, rng.gauss(esperado, esperado * 0.35 + 0.3))
        if vazamento and ts >= vazamento["inicio"]:
            litros += vazamento["litros_hora"] * rng.uniform(0.95, 1.05)
        acumulado += round(litros)
        saida.append((ts, acumulado))
    return saida


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dias", type=int, default=90)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--fim", help="data final (YYYY-MM-DD, exclusiva); padrão: hoje")
    args = ap.parse_args()

    fim = datetime.fromisoformat(args.fim) if args.fim else datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    inicio = fim - timedelta(days=args.dias)
    horas = args.dias * 24
    rng = random.Random(args.seed)

    db = SessionLocal()
    try:
        hidrometros = garantir_estrutura(db)
        print(f"{len(hidrometros)} hidrômetros. Gerando {args.dias} dias ({inicio:%Y-%m-%d} a {fim:%Y-%m-%d})...")

        escolhidos = rng.sample(range(len(hidrometros)), min(UNIDADES_COM_VAZAMENTO, len(hidrometros)))
        vazamentos = {}
        for idx in escolhidos:
            # Começa entre 25% e 80% do período, para haver "antes" e "depois" no gráfico.
            dia_inicio = rng.randint(args.dias // 4, int(args.dias * 0.8))
            vazamentos[idx] = {"inicio": inicio + timedelta(days=dia_inicio), "litros_hora": rng.randint(4, 12)}

        db.query(Leitura).filter(Leitura.hidrometro_id.in_([h.id for h in hidrometros])).delete(synchronize_session=False)
        db.commit()

        lote = []
        total = 0
        for idx, hidrometro in enumerate(hidrometros):
            serie = simular_hidrometro(rng, inicio, horas, vazamentos.get(idx))
            ant_litros = ant_ts = None
            for ts, acumulado in serie:
                lote.append(
                    {
                        "hidrometro_id": hidrometro.id,
                        "timestamp": ts,
                        "litros_acumulados": acumulado,
                        "vazao_instantanea": calcular_vazao(ant_litros, ant_ts, acumulado, ts),
                    }
                )
                ant_litros, ant_ts = acumulado, ts
            if len(lote) >= 20_000:
                db.execute(insert(Leitura), lote)
                total += len(lote)
                lote = []
        if lote:
            db.execute(insert(Leitura), lote)
            total += len(lote)
        db.commit()

        gabarito = [
            {
                "hidrometroId": hidrometros[i].id,
                "unidadeId": hidrometros[i].unidade_id,
                "numeroSerie": hidrometros[i].numero_serie,
                "inicio": v["inicio"].isoformat(),
                "litrosPorHora": v["litros_hora"],
            }
            for i, v in sorted(vazamentos.items())
        ]
        destino = Path(__file__).resolve().parent / "vazamentos_injetados.json"
        destino.write_text(json.dumps(gabarito, indent=2, ensure_ascii=False), encoding="utf-8")

        print(f"{total} leituras gravadas.")
        print(f"Vazamentos injetados em {len(gabarito)} unidades (gabarito em {destino.name}):")
        for g in gabarito:
            print(f"  hidrômetro {g['numeroSerie']}: ~{g['litrosPorHora']} L/h desde {g['inicio'][:10]}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
