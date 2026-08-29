"""Previsao do tempo pela posicao do layout (fase 10 do plano).

**Decisao do Lucas, 29/08 (delegada): Open-Meteo como default.** Sem chave,
sem cadastro, sem cartao. A tela quer temperatura de ar e vento na proxima
janela de horas, nao radar nem alerta.

**Incidente em producao, 29/08:** o container do Railway devolveu 502 porque
o Open-Meteo respondeu 429 (`Daily API request limit exceeded`). Da maquina
do Lucas o mesmo request funciona. O Open-Meteo limita por IP, e o IP de
saida do Railway e compartilhado entre varios clientes da plataforma: a cota
diaria ja chega estourada mesmo sem o nosso trafego. Nao e bug de codigo, e
escolha de provedor incompativel com hospedagem de IP compartilhado.

Tres mudancas em resposta:
  1. cache PERSISTENTE no Postgres (`clima_cache`), nao mais um dict do
     processo: uma busca boa serve todos os clientes e sobrevive a deploy,
     o que reduz muito o consumo da cota que resta.
  2. quando a fonte falha e existe cache (mesmo vencido), serve o dado velho
     com a idade declarada em vez de 502. So erra quando nao ha NADA salvo.
  3. suporte opcional ao OpenWeather: se `SARU_OPENWEATHER_KEY` estiver
     setada, usa ele em vez do Open-Meteo. O free tier do OpenWeather limita
     por CHAVE, nao por IP, entao nao sofre do mesmo problema. As duas fontes
     sao normalizadas pro mesmo shape aqui: o resto do sistema nao sabe qual
     foi usada.

**Adicao em 29/08 (mesmo dia): met.no como fallback de cascata.** Chave do
OpenWeather nunca foi setada e o cache comecou vazio, entao as duas
mitigacoes acima nao tinham de onde servir no primeiro 429. O met.no
(Instituto Meteorologico da Noruega) e gratuito, sem cadastro, e limita por
User-Agent identificado em vez de IP: nao sofre o problema do IP
compartilhado do Railway. Cascata final: OpenWeather se a chave existir,
senao Open-Meteo; se o primario falhar, met.no entra ANTES de recorrer ao
cache velho. So quando os dois (primario + met.no) falharem e que
`previsao` cai pro cache vencido ou pro erro. Cada provedor agora declara
`fonte` no payload (campo aditivo, o front nao precisa saber qual respondeu).

O que este modulo emite e `TempoComPrevisao` do `contract.ts` mais os campos
novos `buscado_em`, `defasado` e `fonte` (acrescentar e seguro, o front so le
o que conhece). Temperatura de PISTA nao vem daqui: nenhum servico de
meteorologia mede asfalto. O box continua estimando pista a partir do ar, e a
tela continua dizendo que essa e uma estimativa, o que ja fazia.

TTL de 15 minutos porque a tela atualiza a cada 15 (fase 10) e o dado da
fonte muda de hora em hora: dentro do TTL a resposta sai so do Postgres, sem
tocar a fonte.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx
from psycopg.types.json import Jsonb

from .config import CONFIG
from .db import connect

_TTL_S = 15 * 60

# WMO weather code (Open-Meteo) -> texto. So os codigos que importam pra
# pista; o resto cai no default. Chuva e o unico que muda decisao de pneu,
# entao os codigos de precipitacao sao os mais detalhados aqui.
_CONDICAO_OPEN_METEO = {
    0: "céu limpo", 1: "predominantemente limpo", 2: "parcialmente nublado", 3: "nublado",
    45: "nevoeiro", 48: "nevoeiro com geada",
    51: "garoa fraca", 53: "garoa", 55: "garoa forte",
    61: "chuva fraca", 63: "chuva", 65: "chuva forte",
    80: "pancada fraca", 81: "pancada", 82: "pancada forte",
    95: "trovoada", 96: "trovoada com granizo", 99: "trovoada com granizo",
}


def _texto_open_meteo(codigo: int | None) -> str | None:
    if codigo is None:
        return None
    return _CONDICAO_OPEN_METEO.get(int(codigo), "condição não catalogada")


# symbol_code do met.no (https://api.met.no/weatherapi/weathericon/2.0/)
# -> texto. Os codigos vem com sufixo de periodo (_day, _night,
# _polartwilight) que e removido antes de olhar aqui, senao a tabela
# triplicaria de tamanho pra dizer a mesma coisa. So os que a tela precisa:
# limpo, nuvem, nevoa e as variacoes de chuva/pancada/trovoada/neve que
# mudam decisao de pneu.
_CONDICAO_METNO = {
    "clearsky": "céu limpo",
    "fair": "poucas nuvens",
    "partlycloudy": "parcialmente nublado",
    "cloudy": "nublado",
    "fog": "névoa",
    "lightrain": "chuva fraca",
    "rain": "chuva",
    "heavyrain": "chuva forte",
    "lightrainshowers": "pancada fraca",
    "rainshowers": "pancada",
    "heavyrainshowers": "pancada forte",
    "lightsleet": "chuva com neve fraca",
    "sleet": "chuva com neve",
    "heavysleet": "chuva com neve forte",
    "lightsleetshowers": "pancada de chuva com neve fraca",
    "sleetshowers": "pancada de chuva com neve",
    "heavysleetshowers": "pancada de chuva com neve forte",
    "lightsnow": "neve fraca",
    "snow": "neve",
    "heavysnow": "neve forte",
    "lightsnowshowers": "pancada de neve fraca",
    "snowshowers": "pancada de neve",
    "heavysnowshowers": "pancada de neve forte",
    "thunder": "trovoada",
    "lightrainandthunder": "chuva fraca com trovoada",
    "rainandthunder": "chuva com trovoada",
    "heavyrainandthunder": "chuva forte com trovoada",
    "rainshowersandthunder": "pancada com trovoada",
    "lightrainshowersandthunder": "pancada fraca com trovoada",
    "heavyrainshowersandthunder": "pancada forte com trovoada",
    "sleetandthunder": "chuva com neve e trovoada",
    "lightsleetandthunder": "chuva com neve fraca e trovoada",
    "heavysleetandthunder": "chuva com neve forte e trovoada",
    "sleetshowersandthunder": "pancada de chuva com neve e trovoada",
    "snowandthunder": "neve com trovoada",
    "lightsnowandthunder": "neve fraca com trovoada",
    "heavysnowandthunder": "neve forte com trovoada",
    "snowshowersandthunder": "pancada de neve com trovoada",
}


def _texto_metno(symbol_code: str | None) -> str | None:
    if not symbol_code:
        return None
    # o sufixo de periodo do dia nao muda a condicao, so a luz: tira antes
    # de procurar na tabela.
    base = symbol_code
    for sufixo in ("_polartwilight", "_day", "_night"):
        if base.endswith(sufixo):
            base = base[: -len(sufixo)]
            break
    return _CONDICAO_METNO.get(base, "condição não catalogada")


def _buscar_open_meteo(lat: float, lon: float, horas: int) -> dict[str, Any]:
    """`dict` normalizado (sem `buscado_em`/`defasado`, isso quem poe e `previsao`).

    Levanta `httpx.HTTPError` se a fonte falhar (inclui o 429 do incidente).
    """
    resposta = httpx.get(
        CONFIG.clima_base,
        params={
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,wind_speed_10m,weather_code",
            "hourly": "temperature_2m,weather_code",
            "wind_speed_unit": "kmh",
            "forecast_days": 2,
            "timezone": "auto",
        },
        timeout=8.0,
    )
    resposta.raise_for_status()
    bruto = resposta.json()

    atual = bruto.get("current") or {}
    horario = bruto.get("hourly") or {}
    tempos = horario.get("time") or []
    temps = horario.get("temperature_2m") or []
    codigos = horario.get("weather_code") or []

    # a serie comeca na hora atual, nao na meia-noite: a tela pergunta "como
    # vai estar na minha bateria", e bateria e daqui a pouco
    agora_iso = str(atual.get("time") or "")
    inicio = next((i for i, t in enumerate(tempos) if t >= agora_iso), 0)
    fatia = slice(inicio, inicio + horas)

    return {
        "temperatura_atual_c": float(atual.get("temperature_2m") or 0.0),
        "vento_kmh": float(atual.get("wind_speed_10m")) if atual.get("wind_speed_10m") is not None else None,
        "condicao_atual": _texto_open_meteo(atual.get("weather_code")),
        "previsao_horaria": [
            {"horario": t, "temperatura_c": float(c), "condicao": _texto_open_meteo(w)}
            for t, c, w in zip(tempos[fatia], temps[fatia], codigos[fatia], strict=False)
        ],
        "fonte": "open-meteo",
    }


def _buscar_openweather(lat: float, lon: float, horas: int) -> dict[str, Any]:
    """Mesmo shape de `_buscar_open_meteo`, fonte diferente.

    Usa os endpoints gratuitos (weather + forecast de 3 em 3h), nao o
    One Call 3.0 que virou pago. `lang=pt_br` poupa mapear codigo pra texto:
    o OpenWeather ja devolve a descricao em portugues.

    Simplificacao assumida (fallback, nao e o caminho principal): o
    `dt_txt` do forecast vem em UTC, sem conversao pro fuso local do layout
    como o Open-Meteo faz com `timezone=auto`. Pra decisao de pneu na
    proxima janela de horas isso nao muda o numero, so o rotulo da hora.
    """
    params_base = {"lat": lat, "lon": lon, "appid": CONFIG.openweather_key, "units": "metric", "lang": "pt_br"}

    atual_resp = httpx.get(CONFIG.openweather_clima_base, params=params_base, timeout=8.0)
    atual_resp.raise_for_status()
    atual = atual_resp.json()

    previsao_resp = httpx.get(CONFIG.openweather_previsao_base, params=params_base, timeout=8.0)
    previsao_resp.raise_for_status()
    bruto_previsao = previsao_resp.json()

    lista = bruto_previsao.get("list") or []
    # cada item cobre 3h; pra cobrir a mesma janela em horas, pega
    # ceil(horas / 3) itens (minimo 1)
    quantidade = max(1, -(-horas // 3))

    vento_ms = (atual.get("wind") or {}).get("speed")
    return {
        "temperatura_atual_c": float((atual.get("main") or {}).get("temp") or 0.0),
        "vento_kmh": round(float(vento_ms) * 3.6, 1) if vento_ms is not None else None,
        "condicao_atual": ((atual.get("weather") or [{}])[0]).get("description"),
        "previsao_horaria": [
            {
                "horario": str(item.get("dt_txt") or "").replace(" ", "T")[:16],
                "temperatura_c": float((item.get("main") or {}).get("temp") or 0.0),
                "condicao": ((item.get("weather") or [{}])[0]).get("description"),
            }
            for item in lista[:quantidade]
        ],
        "fonte": "openweather",
    }


def _buscar_metno(lat: float, lon: float, horas: int) -> dict[str, Any]:
    """Mesmo shape dos outros, fonte met.no. Ultimo fallback da cascata.

    Sem chave, mas o header `User-Agent` e obrigatorio pelos termos de uso
    deles (identifica app + contato); sem ele a resposta e bloqueada. E
    assim que o met.no limita uso, no lugar de IP ou chave, o que o deixa
    imune ao 429 compartilhado que motivou este fallback.
    """
    resposta = httpx.get(
        CONFIG.metno_base,
        params={"lat": lat, "lon": lon},
        headers={"User-Agent": CONFIG.metno_user_agent},
        timeout=8.0,
    )
    resposta.raise_for_status()
    bruto = resposta.json()

    serie = ((bruto.get("properties") or {}).get("timeseries")) or []
    if not serie:
        raise httpx.HTTPError("met.no respondeu sem timeseries")

    def _instante(item: dict[str, Any]) -> datetime | None:
        bruto_tempo = str(item.get("time") or "")
        try:
            return datetime.fromisoformat(bruto_tempo.replace("Z", "+00:00"))
        except ValueError:
            return None

    def _detalhes(item: dict[str, Any]) -> dict[str, Any]:
        return ((item.get("data") or {}).get("instant") or {}).get("details") or {}

    def _simbolo(item: dict[str, Any]) -> str | None:
        # symbol_code so vem em next_1_hours (as vezes so em next_6_hours,
        # nos ultimos itens da serie); sem ele a condicao fica None, o que
        # e honesto, nao um chute.
        resumo = ((item.get("data") or {}).get("next_1_hours") or {}).get("summary") or {}
        return resumo.get("symbol_code")

    # a serie do met.no vem de hora em hora nas proximas horas: corta a
    # partir de agora ate `horas` adiante, igual ao Open-Meteo faz com o
    # slice por `agora_iso` la em cima.
    agora = datetime.now(timezone.utc)
    futuros = [item for item in serie if (t := _instante(item)) is not None and t >= agora]
    fatia = (futuros or serie)[:horas]

    primeiro = fatia[0] if fatia else serie[0]
    detalhes_atual = _detalhes(primeiro)
    vento_ms = detalhes_atual.get("wind_speed")

    return {
        "temperatura_atual_c": float(detalhes_atual.get("air_temperature") or 0.0),
        "vento_kmh": round(float(vento_ms) * 3.6, 1) if vento_ms is not None else None,
        "condicao_atual": _texto_metno(_simbolo(primeiro)),
        "previsao_horaria": [
            {
                "horario": str(item.get("time") or "")[:16],
                "temperatura_c": float(_detalhes(item).get("air_temperature") or 0.0),
                "condicao": _texto_metno(_simbolo(item)),
            }
            for item in fatia
        ],
        "fonte": "met.no",
    }


def _buscar(lat: float, lon: float, horas: int) -> dict[str, Any]:
    """Cascata de provedores (incidente 29/08, ver docstring do modulo).

    Primario: OpenWeather se a chave existir (limite por chave), senao
    Open-Meteo (limite por IP, a causa do 429 em producao). Se o primario
    falhar, met.no entra antes de desistir: ele limita por User-Agent, nao
    por IP nem chave, entao nao herda o problema de nenhum dos dois. Se os
    dois falharem, propaga o erro do met.no (o ultimo tentado); quem decide
    servir cache vencido em vez de estourar 502 e `previsao`, nao aqui.
    """
    primario = _buscar_openweather if CONFIG.openweather_key else _buscar_open_meteo
    try:
        return primario(lat, lon, horas)
    except httpx.HTTPError:
        return _buscar_metno(lat, lon, horas)


def _ler_cache(lat_chave: float, lon_chave: float) -> tuple[dict[str, Any], datetime] | None:
    with connect(autocommit=True) as conn:
        linha = conn.execute(
            "select payload, buscado_em from clima_cache where latitude = %s and longitude = %s",
            (lat_chave, lon_chave),
        ).fetchone()
    if not linha:
        return None
    payload, buscado_em = linha
    return payload, buscado_em


def _salvar_cache(lat_chave: float, lon_chave: float, payload: dict[str, Any], agora: datetime) -> None:
    with connect(autocommit=True) as conn:
        conn.execute(
            """
            insert into clima_cache (latitude, longitude, payload, buscado_em)
            values (%s, %s, %s, %s)
            on conflict (latitude, longitude)
            do update set payload = excluded.payload, buscado_em = excluded.buscado_em
            """,
            (lat_chave, lon_chave, Jsonb(payload), agora),
        )


def _no_fuso_da_pista(dado: dict[str, Any], fuso: str | None) -> dict[str, Any]:
    """Reescreve os horarios no fuso DA PISTA, com o deslocamento explicito.

    Duas coisas estavam erradas e viraram uma so na tela. O met.no devolve UTC e
    o codigo cortava o `Z`, entao saia `2026-08-29T11:00`, um horario UTC
    vestido de horario sem fuso; o front fazia `new Date` nessa string, que o
    JavaScript interpreta como hora LOCAL, e mostrava 11h quando na pista eram
    8h. Tres horas de erro, exatamente o offset de Brasilia.

    A correcao nao e so marcar o fuso: e usar o fuso da PISTA. Quem le esta no
    box, e a pergunta e "que temperatura vai fazer na minha bateria", nao "que
    horas sao no computador de quem abriu a tela". `pista.timezone` ja existe no
    catalogo desde a primeira migration e nunca tinha sido usado.

    Sai em ISO 8601 COM deslocamento (`2026-08-29T08:00:00-03:00`), que e o
    unico formato sem ambiguidade: `new Date` acerta, e ninguem precisa saber de
    que fuso veio.
    """
    if not fuso:
        return dado
    try:
        from zoneinfo import ZoneInfo

        tz = ZoneInfo(fuso)
    except Exception:  # noqa: BLE001
        # fuso invalido no catalogo nao pode derrubar a previsao inteira
        return dado

    def converter(iso: str) -> str:
        try:
            d = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        except ValueError:
            return iso
        # timestamp sem fuso nesta altura veio de fonte que responde em UTC
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d.astimezone(tz).isoformat()

    return {
        **dado,
        "fuso": fuso,
        "previsao_horaria": [
            {**p, "horario": converter(str(p.get("horario") or ""))}
            for p in dado.get("previsao_horaria") or []
        ],
    }


def previsao(lat: float, lon: float, horas: int = 12, fuso: str | None = None) -> dict[str, Any]:
    """`TempoComPrevisao` pra uma coordenada, mais `buscado_em` e `defasado`.

    Dentro do TTL a resposta sai so do cache do Postgres, sem tocar a fonte.
    Fora do TTL tenta buscar de novo; se a fonte falhar e houver cache (mesmo
    vencido), serve ele com `defasado=True` em vez de propagar o erro. So
    levanta `httpx.HTTPError` quando a fonte falha E nao ha nada em cache:
    dado velho marcado como velho e melhor que erro, dado velho disfarcado de
    novo e a doenca que este projeto nao comete.
    """
    lat_chave, lon_chave = round(lat, 3), round(lon, 3)
    agora = datetime.now(timezone.utc)

    cache = _ler_cache(lat_chave, lon_chave)
    if cache is not None:
        payload, buscado_em = cache
        if (agora - buscado_em).total_seconds() < _TTL_S:
            return _no_fuso_da_pista(
                {**payload, "buscado_em": buscado_em.isoformat(), "defasado": False}, fuso
            )

    try:
        dado = _buscar(lat, lon, horas)
    except httpx.HTTPError:
        if cache is not None:
            payload, buscado_em = cache
            return _no_fuso_da_pista(
                {**payload, "buscado_em": buscado_em.isoformat(), "defasado": True}, fuso
            )
        raise

    # o cache guarda o dado CRU da fonte, sem fuso aplicado: a mesma coordenada
    # pode servir layouts diferentes, e converter na leitura mantem o cache util
    _salvar_cache(lat_chave, lon_chave, dado, agora)
    return _no_fuso_da_pista({**dado, "buscado_em": agora.isoformat(), "defasado": False}, fuso)
