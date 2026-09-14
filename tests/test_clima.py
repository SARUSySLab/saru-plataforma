"""Resiliencia do clima (incidente 29/08: 429 do Open-Meteo no Railway).

Os tres comportamentos que a fase de resiliencia precisa provar:

  1. cache dentro do TTL serve sem chamar a fonte (o motivo de existir:
     reduzir consumo da cota compartilhada);
  2. fonte fora do ar com cache vencido ainda serve, marcado `defasado`;
  3. sem NADA em cache, a falha da fonte propaga (isso quem transforma em
     502 e a rota, nao este modulo).

Roda contra o Postgres real da PoC, no mesmo padrao de `tests/test_api.py`:
sem rede real pra fonte de clima, `_buscar` e sempre monkeypatchado.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import httpx
import pytest

from saru_poc import clima
from saru_poc.db import connect

# Deslocamento pequeno e unico por teste pra nunca colidir de linha no cache,
# mesmo rodando o modulo duas vezes seguidas.
_LAT_BASE, _LON_BASE = -23.500, -46.500


@pytest.fixture
def postgres():
    try:
        from saru_poc.db import ping

        ping()
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"postgres indisponivel: {e}")


@pytest.fixture
def coordenada(postgres):
    """Uma coordenada nova por teste, e limpa o cache dela ao final."""
    # deriva um deslocamento pequeno e estavel a partir de um uuid, garante
    # que dois testes rodando em paralelo (ou o mesmo teste duas vezes) nunca
    # colidem na mesma chave (latitude, longitude)
    deslocamento = (uuid4().int % 900) / 1000  # 0.000..0.899
    lat = round(_LAT_BASE + deslocamento, 3)
    lon = round(_LON_BASE, 3)
    yield lat, lon
    with connect(autocommit=True) as conn:
        conn.execute(
            "delete from clima_cache where latitude = %s and longitude = %s", (lat, lon)
        )


def _payload_fake() -> dict:
    return {
        "temperatura_atual_c": 21.5,
        "vento_kmh": 8.0,
        "condicao_atual": "céu limpo",
        "previsao_horaria": [{"horario": "2026-08-29T12:00", "temperatura_c": 22.0, "condicao": "céu limpo"}],
    }


def test_cache_dentro_do_ttl_serve_sem_chamar_a_fonte(coordenada, monkeypatch) -> None:
    lat, lon = coordenada
    agora = datetime.now(timezone.utc)
    clima._salvar_cache(lat, lon, _payload_fake(), agora)

    def _buscar_nao_deveria_ser_chamado(*a, **k):
        raise AssertionError("_buscar foi chamado com cache fresco em TTL")

    monkeypatch.setattr(clima, "_buscar", _buscar_nao_deveria_ser_chamado)

    resultado = clima.previsao(lat, lon)

    assert resultado["temperatura_atual_c"] == 21.5
    assert resultado["defasado"] is False
    assert resultado["buscado_em"] == agora.isoformat()


def test_fonte_fora_do_ar_serve_cache_vencido_marcado_como_velho(coordenada, monkeypatch) -> None:
    lat, lon = coordenada
    velho = datetime.now(timezone.utc) - timedelta(hours=3)
    clima._salvar_cache(lat, lon, _payload_fake(), velho)

    def _buscar_falha(*a, **k):
        raise httpx.HTTPStatusError(
            "429", request=httpx.Request("GET", "https://x"), response=httpx.Response(429)
        )

    monkeypatch.setattr(clima, "_buscar", _buscar_falha)

    resultado = clima.previsao(lat, lon)

    assert resultado["temperatura_atual_c"] == 21.5
    assert resultado["defasado"] is True
    assert resultado["buscado_em"] == velho.isoformat()


def test_sem_cache_nenhum_falha_da_fonte_propaga(coordenada, monkeypatch) -> None:
    lat, lon = coordenada
    # nao grava nada em clima_cache pra essa coordenada

    def _buscar_falha(*a, **k):
        raise httpx.HTTPStatusError(
            "429", request=httpx.Request("GET", "https://x"), response=httpx.Response(429)
        )

    monkeypatch.setattr(clima, "_buscar", _buscar_falha)

    with pytest.raises(httpx.HTTPError):
        clima.previsao(lat, lon)


def test_busca_bem_sucedida_atualiza_o_cache(coordenada, monkeypatch) -> None:
    lat, lon = coordenada

    monkeypatch.setattr(clima, "_buscar", lambda *a, **k: _payload_fake())

    resultado = clima.previsao(lat, lon)

    assert resultado["defasado"] is False
    salvo = clima._ler_cache(lat, lon)
    assert salvo is not None
    payload, buscado_em = salvo
    assert payload["temperatura_atual_c"] == 21.5
    assert buscado_em.isoformat() == resultado["buscado_em"]


def _falha_429(*a, **k):
    raise httpx.HTTPStatusError(
        "429", request=httpx.Request("GET", "https://x"), response=httpx.Response(429)
    )


# Cascata de fallback (addendum do incidente 29/08, mesmo dia): met.no entra
# quando o primario (aqui, Open-Meteo, ja que SARU_OPENWEATHER_KEY nao esta
# setada no ambiente de teste) falha. `_buscar` roda de verdade nesses tres
# testes, so os provedores de rede (`_buscar_open_meteo`/`_buscar_metno`) sao
# monkeypatchados: e a cascata em si que esta sob teste, nao o cache.


def test_open_meteo_falha_e_metno_responde(coordenada, monkeypatch) -> None:
    lat, lon = coordenada
    payload_metno = {**_payload_fake(), "fonte": "met.no"}

    monkeypatch.setattr(clima, "_buscar_open_meteo", _falha_429)
    monkeypatch.setattr(clima, "_buscar_metno", lambda *a, **k: payload_metno)

    resultado = clima.previsao(lat, lon)

    assert resultado["fonte"] == "met.no"
    assert resultado["temperatura_atual_c"] == 21.5
    assert resultado["defasado"] is False


def test_open_meteo_e_metno_falham_serve_cache_vencido(coordenada, monkeypatch) -> None:
    lat, lon = coordenada
    velho = datetime.now(timezone.utc) - timedelta(hours=3)
    clima._salvar_cache(lat, lon, _payload_fake(), velho)

    monkeypatch.setattr(clima, "_buscar_open_meteo", _falha_429)
    monkeypatch.setattr(clima, "_buscar_metno", _falha_429)

    resultado = clima.previsao(lat, lon)

    assert resultado["defasado"] is True
    assert resultado["temperatura_atual_c"] == 21.5
    assert resultado["buscado_em"] == velho.isoformat()


def test_open_meteo_e_metno_falham_sem_cache_propaga(coordenada, monkeypatch) -> None:
    lat, lon = coordenada
    # nao grava nada em clima_cache pra essa coordenada

    monkeypatch.setattr(clima, "_buscar_open_meteo", _falha_429)
    monkeypatch.setattr(clima, "_buscar_metno", _falha_429)

    with pytest.raises(httpx.HTTPError):
        clima.previsao(lat, lon)


def test_texto_metno_traduz_e_remove_sufixo_de_periodo() -> None:
    assert clima._texto_metno("clearsky_day") == "céu limpo"
    assert clima._texto_metno("clearsky_night") == "céu limpo"
    assert clima._texto_metno("partlycloudy_polartwilight") == "parcialmente nublado"
    assert clima._texto_metno("cloudy") == "nublado"
    assert clima._texto_metno("fog") == "névoa"
    assert clima._texto_metno("lightrain") == "chuva fraca"
    assert clima._texto_metno("rain") == "chuva"
    assert clima._texto_metno("heavyrain") == "chuva forte"
    assert clima._texto_metno("rainshowers_day") == "pancada"
    assert clima._texto_metno("thunder") == "trovoada"
    assert clima._texto_metno("snow") == "neve"
    assert clima._texto_metno("codigo-nunca-visto") == "condição não catalogada"
    assert clima._texto_metno(None) is None
