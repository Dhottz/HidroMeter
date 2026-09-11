"""Models SQLAlchemy — fonte única de verdade do schema do banco.

Entrega 1: condominios, blocos, unidades, hidrometros, usuarios e as tabelas
de junção N:N de acesso. leituras/alertas/recomendacoes entram nas entregas
2-4.
"""

import enum
from datetime import datetime, timezone

from sqlalchemy import Enum, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Papel(str, enum.Enum):
    sindico = "sindico"
    morador = "morador"


class Condominio(Base):
    __tablename__ = "condominios"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String)
    endereco: Mapped[str | None] = mapped_column(String, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

    blocos: Mapped[list["Bloco"]] = relationship(back_populates="condominio", cascade="all, delete-orphan")
    usuarios: Mapped[list["UsuarioCondominio"]] = relationship(back_populates="condominio", cascade="all, delete-orphan")


class Bloco(Base):
    __tablename__ = "blocos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String)
    condominio_id: Mapped[int] = mapped_column(ForeignKey("condominios.id", ondelete="CASCADE"))

    condominio: Mapped["Condominio"] = relationship(back_populates="blocos")
    unidades: Mapped[list["Unidade"]] = relationship(back_populates="bloco", cascade="all, delete-orphan")


class Unidade(Base):
    __tablename__ = "unidades"

    id: Mapped[int] = mapped_column(primary_key=True)
    numero: Mapped[str] = mapped_column(String)
    bloco_id: Mapped[int] = mapped_column(ForeignKey("blocos.id", ondelete="CASCADE"))

    bloco: Mapped["Bloco"] = relationship(back_populates="unidades")
    hidrometros: Mapped[list["Hidrometro"]] = relationship(back_populates="unidade", cascade="all, delete-orphan")
    usuarios: Mapped[list["UsuarioUnidade"]] = relationship(back_populates="unidade", cascade="all, delete-orphan")


class Hidrometro(Base):
    __tablename__ = "hidrometros"

    id: Mapped[int] = mapped_column(primary_key=True)
    unidade_id: Mapped[int] = mapped_column(ForeignKey("unidades.id", ondelete="CASCADE"))
    numero_serie: Mapped[str] = mapped_column(String, unique=True)
    litros_por_pulso: Mapped[float] = mapped_column(Float, default=1)

    unidade: Mapped["Unidade"] = relationship(back_populates="hidrometros")


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String, unique=True)
    senha_hash: Mapped[str] = mapped_column(String)
    papel: Mapped[Papel] = mapped_column(Enum(Papel, name="papel"))
    criado_em: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

    condominios: Mapped[list["UsuarioCondominio"]] = relationship(back_populates="usuario", cascade="all, delete-orphan")
    unidades: Mapped[list["UsuarioUnidade"]] = relationship(back_populates="usuario", cascade="all, delete-orphan")


class UsuarioCondominio(Base):
    """Acesso de síndico: quais condomínios administra."""

    __tablename__ = "usuario_condominios"
    __table_args__ = (UniqueConstraint("usuario_id", "condominio_id"),)

    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True)
    condominio_id: Mapped[int] = mapped_column(ForeignKey("condominios.id", ondelete="CASCADE"), primary_key=True)

    usuario: Mapped["Usuario"] = relationship(back_populates="condominios")
    condominio: Mapped["Condominio"] = relationship(back_populates="usuarios")


class UsuarioUnidade(Base):
    """Acesso de morador: quais unidades pode ver."""

    __tablename__ = "usuario_unidades"
    __table_args__ = (UniqueConstraint("usuario_id", "unidade_id"),)

    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True)
    unidade_id: Mapped[int] = mapped_column(ForeignKey("unidades.id", ondelete="CASCADE"), primary_key=True)

    usuario: Mapped["Usuario"] = relationship(back_populates="unidades")
    unidade: Mapped["Unidade"] = relationship(back_populates="usuarios")
