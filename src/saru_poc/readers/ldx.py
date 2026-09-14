"""Leitor de inventario para MoTeC .ldx (formato_id motec_ldx).

O .ldx e o sidecar XML de voltas do .ld (formato ainda sem leitor neste
repo). Fatos medidos no acervo em 2026-08-29 (26 arquivos, 218 a 1343
bytes):

- Estrutura: LDXFile > Layers > Layer > MarkerBlock > MarkerGroup
  [Name="Beacons"] > Marker, e Layer > Details > String[Id,Value].
- Marcador real, ex.:
  <Marker Version="100" ClassName="BCN" Name="5, id=99" Flags="13"
   Time="6.69511000000000000e+08"/>
- O atributo Time esta em MICROSSEGUNDOS desde o inicio do log. Confirmado
  por aritmetica com um par de marcadores reais do acervo:
  731818000 - 669511000 = 62307000 us = 62,307 s, que bate exatamente com o
  "Fastest Time" declarado 1:02.307 entre os beacons 5 e 6 (Fastest Lap=6).
  A volta i vai do beacon i-1 ao beacon i.
- Details traz Total Laps, Fastest Time (formato M:SS.mmm) e Fastest Lap.
- Este formato NAO tem canal nenhum: e sidecar puro. `canais` sai sempre
  como tupla vazia. Todo o valor vai em `bruto` e em `duracao_s`.
- Degradacoes reais do acervo, tratadas sem levantar excecao (ausencia
  declarada em `bruto`, nao erro):
    * bloco Details ausente: 11 dos 26 arquivos.
    * nenhum marcador dentro de MarkerGroup[Name="Beacons"]: 4 dos 26
      arquivos (o enunciado original media 2; a contagem medida direto
      contra o acervo em 2026-08-29 e 4, ver relatorio da tarefa).
    * Fastest Time declarado "0:00.000": 1 arquivo (sessao sem volta
      cronometrada valida).
  Um arquivo sem Details e sem marcador ainda e uma leitura valida: apenas
  um cabecalho pobre em bruto.

Porte: leitura do XML e parse de "M:SS.mmm" adaptados de
saru-app/services/telemetry-api/saru_lapanalyzer/infra/datasources/
ldx_reader.py (commit aa94872 do snapshot tudo_junto/saru-app,
2026-08-26). La o .ldx serve so de oraculo de validacao pro .ld irmao; aqui
ele e lido como formato de primeira classe, com o cabecalho cru completo
preservado (nao so as 3 chaves que o leitor de origem extraia).
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from .base import Cabecalho, ErroDeLeitura, LeitorDeInventario

_MICROSSEGUNDOS_POR_SEGUNDO = 1_000_000.0


def _parse_fastest_time(valor: str) -> float | None:
    """Converte "M:SS.mmm" (ou so segundos) em segundos.

    Devolve None se o formato nao for reconhecido, sem levantar: e um campo
    informativo, nao estrutural.
    """
    v = valor.strip()
    if not v:
        return None
    try:
        if ":" in v:
            minutos, segundos = v.split(":", 1)
            return int(minutos) * 60 + float(segundos)
        return float(v)
    except ValueError:
        return None


class LeitorLdx(LeitorDeInventario):
    """Inventario de sidecar MoTeC .ldx. Sem canal, so metadata de sessao."""

    formato_id = "motec_ldx"
    versao = "1"

    def inspecionar(self, caminho: Path) -> Cabecalho:
        try:
            texto = caminho.read_text(encoding="utf-8")
        except OSError as exc:
            raise ErroDeLeitura(f"nao consegui abrir {caminho}: {exc}") from exc

        try:
            raiz = ET.fromstring(texto)
        except ET.ParseError as exc:
            raise ErroDeLeitura(
                f".ldx malformado (XML invalido) em {caminho}: {exc}"
            ) from exc

        if raiz.tag != "LDXFile":
            raise ErroDeLeitura(
                f".ldx sem elemento raiz LDXFile em {caminho}: raiz e <{raiz.tag}>"
            )

        bruto: dict[str, str] = {}
        for chave, valor in raiz.attrib.items():
            bruto[f"ldxfile_{chave.lower()}"] = valor

        marcadores = []
        for grupo in raiz.iter("MarkerGroup"):
            if grupo.get("Name") != "Beacons":
                continue
            marcadores.extend(grupo.findall("Marker"))

        tempos_us: list[float] = []
        for m in marcadores:
            bruto_time = m.get("Time")
            if bruto_time is None:
                continue
            try:
                tempos_us.append(float(bruto_time))
            except ValueError:
                continue

        if marcadores:
            bruto["beacons_n"] = str(len(marcadores))
            bruto["beacons_time_us_raw"] = ",".join(
                m.get("Time", "") for m in marcadores
            )
        else:
            bruto["beacons_n"] = "0"
            bruto["beacons_ausente"] = "true"

        strings = {s.get("Id"): s.get("Value") for s in raiz.iter("String")}
        detalhes_presentes = raiz.find(".//Details") is not None
        if not detalhes_presentes:
            bruto["details_ausente"] = "true"

        for chave_xml, chave_bruto in (
            ("Total Laps", "total_laps"),
            ("Fastest Lap", "fastest_lap"),
            ("Fastest Time", "fastest_time_raw"),
        ):
            valor = strings.get(chave_xml)
            if valor is not None:
                bruto[chave_bruto] = valor

        fastest_time_s = None
        fastest_time_raw = strings.get("Fastest Time")
        if fastest_time_raw is not None:
            fastest_time_s = _parse_fastest_time(fastest_time_raw)
            if fastest_time_s is None:
                bruto["fastest_time_ilegivel"] = "true"
            elif fastest_time_s == 0.0:
                bruto["fastest_time_zerado"] = "true"

        # Duracao: prefere o ultimo beacon (fim do outing cronometrado). Sem
        # marcador, cai no Fastest Time se ele for positivo, senao fica None
        # (declarar ausencia, nunca inventar).
        duracao_s = None
        if tempos_us:
            duracao_s = round(max(tempos_us) / _MICROSSEGUNDOS_POR_SEGUNDO, 6)
        elif fastest_time_s:
            duracao_s = fastest_time_s

        return Cabecalho(
            formato_id=self.formato_id,
            leitor_versao=self.versao,
            canais=(),
            capturado_em=None,
            duracao_s=duracao_s,
            venue_declarado=None,
            bruto=bruto,
        )
