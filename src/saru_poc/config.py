"""Configuracao do ambiente. Uma fonte so, lida do .env."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(REPO_ROOT / ".env")


def _path(var: str, default: str) -> Path:
    raw = os.getenv(var, default)
    p = Path(raw).expanduser()
    return p if p.is_absolute() else (REPO_ROOT / p).resolve()


@dataclass(frozen=True)
class Config:
    pg_host: str = os.getenv("SARU_PG_HOST", "127.0.0.1")
    pg_port: int = int(os.getenv("SARU_PG_PORT", "5442"))
    pg_db: str = os.getenv("SARU_PG_DB", "saru_poc")
    pg_user: str = os.getenv("SARU_PG_USER", "saru")
    pg_password: str = os.getenv("SARU_PG_PASSWORD", "saru")

    # Amostra nunca entra no Postgres: vai pra Parquet aqui, particionado por
    # gravacao e taxa nativa. serie_amostral guarda so o ponteiro.
    data_root: Path = field(default_factory=lambda: _path("SARU_DATA_ROOT", "./data"))
    acervo_root: Path = field(
        default_factory=lambda: _path("SARU_ACERVO_ROOT", "../dados_telemetria")
    )
    # Snapshot do saru-app, so leitura. A PoC nao escreve nada la.
    app_ref: Path = field(
        default_factory=lambda: _path("SARU_APP_REF", "../tudo_junto/saru-app")
    )

    # --- auth (decisao do Lucas, 29/08) ---
    # O default so vale em dev. Em producao a var e obrigatoria, e `api.py`
    # recusa subir sem ela: segredo de assinatura com valor default e o mesmo
    # que nao ter assinatura, e falhar no boot e melhor do que descobrir isso
    # quando alguem forjar um token.
    jwt_secret: str = os.getenv("SARU_JWT_SECRET", "dev-inseguro-troque-em-producao-0123456789")
    jwt_horas: int = int(os.getenv("SARU_JWT_HORAS", "12"))
    # Cookie so viaja em HTTPS quando isto e 1. Fica 0 em dev (localhost e http).
    cookie_seguro: bool = os.getenv("SARU_COOKIE_SEGURO", "0") == "1"

    # --- Sarue, o assistente de IA ---
    openrouter_key: str | None = os.getenv("SARU_OPENROUTER_KEY") or None
    openrouter_modelo: str = os.getenv("SARU_OPENROUTER_MODELO", "anthropic/claude-sonnet-4.5")

    # --- clima ---
    # Open-Meteo: sem chave, sem cadastro, licenca livre pra uso nao comercial.
    # Trocar de provedor mexe so em `clima.py`.
    clima_base: str = os.getenv("SARU_CLIMA_BASE", "https://api.open-meteo.com/v1/forecast")
    # OpenWeather e o fallback (decisao do Lucas, 29/08): o free tier dele
    # limita por CHAVE, nao por IP, entao nao sofre do 429 compartilhado que o
    # IP de saida do Railway causa no Open-Meteo. So entra em uso se a chave
    # estiver setada; sem ela o comportamento e identico ao de antes.
    openweather_key: str | None = os.getenv("SARU_OPENWEATHER_KEY") or None
    openweather_clima_base: str = os.getenv(
        "SARU_OPENWEATHER_CLIMA_BASE", "https://api.openweathermap.org/data/2.5/weather"
    )
    openweather_previsao_base: str = os.getenv(
        "SARU_OPENWEATHER_PREVISAO_BASE", "https://api.openweathermap.org/data/2.5/forecast"
    )
    # met.no (Instituto Meteorologico da Noruega): ultimo fallback da cascata
    # (decisao do Lucas, 29/08). Sem chave, sem cadastro, e o limite dele e
    # por User-Agent identificado, nao por IP nem por chave, entao nao sofre
    # nem do 429 compartilhado do Railway (Open-Meteo) nem exige cadastro
    # (OpenWeather). O User-Agent e obrigatorio pelos termos de uso deles:
    # sem ele a resposta e bloqueada. Precisa ser ASCII puro, header HTTP nao
    # aceita acento (ja derrubou uma chamada neste projeto antes).
    metno_base: str = os.getenv(
        "SARU_METNO_BASE", "https://api.met.no/weatherapi/locationforecast/2.0/compact"
    )
    metno_user_agent: str = os.getenv(
        "SARU_METNO_USER_AGENT", "SARU-Analyzer/0.1 (contato@lassoftware.com.br)"
    )

    @property
    def em_producao(self) -> bool:
        return os.getenv("SARU_AMBIENTE", "dev") == "producao"

    @property
    def dsn(self) -> str:
        return (
            f"postgresql://{self.pg_user}:{self.pg_password}"
            f"@{self.pg_host}:{self.pg_port}/{self.pg_db}"
        )

    @property
    def parquet_root(self) -> Path:
        return self.data_root / "parquet"


CONFIG = Config()
