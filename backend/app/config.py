import re

from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_duracao_segundos(valor: str) -> int:
    """Converte "1d", "12h", "30m", "45s" ou um número puro (segundos) em segundos."""
    valor = valor.strip().lower()
    match = re.fullmatch(r"(\d+)\s*([smhd]?)", valor)
    if not match:
        raise ValueError(f"Duração inválida: {valor!r}")
    quantidade, unidade = match.groups()
    multiplicadores = {"s": 1, "m": 60, "h": 3600, "d": 86400, "": 1}
    return int(quantidade) * multiplicadores[unidade]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://hidrometer:hidrometer@localhost:5434/hidrometer"
    jwt_secret: str = "changeme-dev-secret"
    jwt_expires_in: str = "1d"
    port: int = 3001

    @property
    def jwt_expires_seconds(self) -> int:
        return parse_duracao_segundos(self.jwt_expires_in)


settings = Settings()
