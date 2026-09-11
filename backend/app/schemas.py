"""DTOs Pydantic. `CamelModel` serializa/aceita JSON em camelCase (blocoId,
numeroSerie, litrosPorPulso...) mesmo com os models SQLAlchemy em snake_case —
mantém o contrato REST idêntico ao que o frontend já consome.
"""

from pydantic import BaseModel, ConfigDict

from app.models import Papel


def to_camel(snake: str) -> str:
    partes = snake.split("_")
    return partes[0] + "".join(p.title() for p in partes[1:])


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)


# ---- Auth ----


class RegisterIn(CamelModel):
    nome: str
    email: str
    senha: str
    papel: Papel
    condominio_id: int | None = None
    unidade_id: int | None = None


class LoginIn(CamelModel):
    email: str
    senha: str


class UsuarioOut(CamelModel):
    id: int
    nome: str
    email: str
    papel: Papel


class TokenOut(CamelModel):
    token: str
    usuario: UsuarioOut


# ---- Condominio ----


class CondominioOut(CamelModel):
    id: int
    nome: str
    endereco: str | None = None


# ---- Bloco ----


class CondominioResumoOut(CamelModel):
    id: int
    nome: str


class BlocoOut(CamelModel):
    id: int
    nome: str
    condominio_id: int
    condominio: CondominioResumoOut


class BlocoCreate(CamelModel):
    nome: str
    condominio_id: int


class BlocoUpdate(CamelModel):
    nome: str


# ---- Hidrometro ----


class HidrometroOut(CamelModel):
    id: int
    unidade_id: int
    numero_serie: str
    litros_por_pulso: float


class HidrometroCreate(CamelModel):
    unidade_id: int
    numero_serie: str
    litros_por_pulso: float | None = None


class HidrometroUpdate(CamelModel):
    numero_serie: str | None = None
    litros_por_pulso: float | None = None


# ---- Unidade ----


class BlocoResumoOut(CamelModel):
    id: int
    nome: str
    condominio_id: int


class UnidadeOut(CamelModel):
    id: int
    numero: str
    bloco_id: int
    bloco: BlocoResumoOut
    hidrometros: list[HidrometroOut]


class UnidadeCreate(CamelModel):
    bloco_id: int
    numero: str | None = None
    numeros: list[str] | None = None


class UnidadeUpdate(CamelModel):
    numero: str
