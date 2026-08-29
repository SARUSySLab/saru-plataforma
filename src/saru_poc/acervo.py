"""Carga do catalogo de acervo a partir do aliases.yaml do saru-app.

Este modulo materializa a decisao do Lucas de 29/08: a variacao por modelo de
logger mora em DADO, nao em codigo. O `aliases.yaml` do saru-app (22 perfis,
306 linhas de mapeamento, 61 canais canonicos) e a fonte, e vira linha em
`grandeza`, `canal_canonico`, `perfil_origem`, `mapa_canal` e
`mapeamento_canal`.

A PoC nunca escreve no saru-app: o arquivo e lido do snapshot em modo leitura.

Duas correcoes aplicadas na carga, as duas decididas em 29/08:

1. A chave de `mapeamento_canal` e a coluna bruta, nao o canal canonico. 35 das
   306 linhas aceitam mais de um nome de coluna, e cada nome vira uma linha.
2. `normalize_by_max` nao entra. Os 9 freios que usavam normalizacao pelo
   maximo do proprio arquivo passam a alimentar `brake_press`, em pressao de
   verdade (todos chegam em bar, canonizados pra kPa). Quem precisa de 0 a 1
   normaliza na analise, declarando contra o que normalizou.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .config import CONFIG
from .readers import FORMATOS_POR_ID, LEITORES

# Uma grandeza por unidade canonica distinta encontrada no aliases.yaml. Nao ha
# invencao aqui: as 14 sairam da varredura das 306 linhas. `angulo_grau` e
# `angulo_rad` ficam separadas porque o catalogo determina que grandeza carrega
# UMA unidade canonica, e o arquivo usa deg pra GPS e rad pra esterco.
UNIDADE_PARA_GRANDEZA: dict[str, tuple[str, str, str]] = {
    "-": ("adimensional", "Adimensional", "1"),
    "0-1": ("fracao", "Fracao de 0 a 1", "1"),
    "m/s": ("velocidade", "Velocidade", "m.s-1"),
    "m": ("comprimento", "Comprimento", "m"),
    "°C": ("temperatura", "Temperatura", "K"),
    "m/s2": ("aceleracao", "Aceleracao", "m.s-2"),
    "rpm": ("rotacao", "Rotacao", "min-1"),
    "deg": ("angulo_grau", "Angulo em grau", "rad"),
    "rad": ("angulo_rad", "Angulo em radiano", "rad"),
    "rad/s": ("velocidade_angular", "Velocidade angular", "rad.s-1"),
    "kPa": ("pressao", "Pressao", "Pa"),
    "N": ("forca", "Forca", "N"),
    "Nm": ("torque", "Torque", "N.m"),
    "s": ("tempo", "Tempo", "s"),
}

# Perfil do aliases.yaml -> formato do catalogo.
#
# Decisao do Lucas de 29/08, segunda rodada: o lastro que um PERFIL precisa e
# do proprio perfil, nao do formato. Formato e container e precisa de
# assinatura medida; perfil e vocabulario e precisa de arquivo real cujos
# canais casem com ele.
#
# A primeira versao conflava as duas coisas e pulava 14 perfis, entre eles
# `acc` e `gt7_ld`, que juntos tem 37 arquivos reais no acervo. O resultado foi
# 37 dos 42 `.ld` ficarem com 100% dos canais sem mapa, porque o container
# `.ld` carrega tres vocabularios diferentes e so um estava semeado.
#
# Um formato pode ter VARIOS perfis. Quem escolhe em runtime e a heuristica de
# sobreposicao de nome de canal, em `pipeline/ingestao.py`.
PERFIL_PARA_FORMATO: dict[str, str] = {
    "aim_xrk": "aim_xrk",
    "aim_drk": "aim_drk",
    "aim_gpk": "aim_gpk",
    "motec_ld": "motec_ld",
    "vbox": "vbox_vbo",
    "listhead_dat": "pi_listhead_dat",
    "pi_pid": "pi_pid",
    # O perfil chamado `aim` no saru-app e o que le `.dlf`. O Manual de Campo
    # conclui que o `.dlf` e Pro Tune TDL, nao AiM. O id do perfil fica como
    # esta pra nao divergir da fonte, e a divergencia vai na nota.
    "aim": "protune_dlf",
    # Vocabularios adicionais do container `.ld`, medidos no acervo em 29/08
    # por sobreposicao de nome de canal contra o aliases.yaml:
    #   acc     34 arquivos, mediana 39 de 55 canais casando (71%), margem 38
    #   gt7_ld   3 arquivos, mediana 23 de 37 canais casando (62%), margem 12
    # Sao simulados, e por isso `perfil_origem.simulado` marca os dois: a regua
    # de analise de sim nao e a de logger real.
    "acc": "motec_ld",
    "gt7_ld": "motec_ld",
}

MOTIVO_PULADO: dict[str, str] = {
    ".pi_core": "ancora YAML compartilhada, nao e perfil",
    "iracing": "simulador",
    "gt7": "simulador",
    "ams2": "simulador",
    "saru_lts": "saida do proprio simulador do SARU",
    "saru_gt7": "saida do gateway GT7 do SARU",
    "fueltech": "CSV sem amostra medida no acervo, bloqueado pelo pedido ao Saru",
    "protune": "CSV sem amostra medida no acervo, bloqueado pelo pedido ao Saru",
    "pitoolbox": "CSV sem amostra medida no acervo",
    "windarab": "CSV sem amostra medida (o acervo tem .bmsbin binario, nao o CSV)",
    "wintax": "CSV sem amostra medida no acervo",
    "trackaddict": "CSV sem amostra medida no acervo",
}

SIMULADOS = {"acc", "iracing", "gt7", "gt7_ld", "ams2", "saru_lts", "saru_gt7"}

CANTOS = ("fl", "fr", "rl", "rr")
PONTOS = ("inner", "mid", "outer")

BAR_PARA_KPA = 100.0


@dataclass
class Resumo:
    grandezas: int = 0
    canais: int = 0
    perfis: int = 0
    mapeamentos: int = 0
    formatos: int = 0
    pulados: list[str] | None = None
    reescritos: list[str] | None = None


def caminho_aliases() -> Path:
    return (
        CONFIG.app_ref
        / "services/telemetry-api/saru_lapanalyzer/infra/mapping/aliases.yaml"
    )


def _decompor(canal: str) -> tuple[str | None, str | None]:
    """Extrai canto (fl, fr, rl, rr) e ponto (inner, mid, outer) do nome."""
    canto = next((c for c in CANTOS if canal.endswith(f"_{c}")), None)
    ponto = next((p for p in PONTOS if f"_{p}_" in canal), None)
    return canto, ponto


def ler_aliases(caminho: Path | None = None) -> dict[str, dict[str, Any]]:
    bruto = yaml.safe_load((caminho or caminho_aliases()).read_text(encoding="utf-8"))
    return {
        p: canais
        for p, canais in bruto.items()
        if isinstance(canais, dict)
        and all(isinstance(v, dict) for v in canais.values())
    }


def semear(conn, mapa_versao: str = "2026.08-1") -> Resumo:
    """Popula o catalogo de acervo. Idempotente: roda de novo sem duplicar."""
    perfis = ler_aliases()
    resumo = Resumo(pulados=[], reescritos=[])

    with conn.transaction():
        for fmt in FORMATOS_POR_ID.values():
            conn.execute(
                """insert into formato_telemetria
                     (id, rotulo, fabricante, extensao_tipica, assinatura,
                      binario, leitor, leitor_ref)
                   values (%s,%s,%s,%s,%s,%s,%s,%s)
                   on conflict (id) do update set
                     rotulo         = excluded.rotulo,
                     fabricante     = excluded.fabricante,
                     assinatura     = excluded.assinatura,
                     binario        = excluded.binario,
                     leitor         = excluded.leitor,
                     leitor_ref     = excluded.leitor_ref""",
                (
                    fmt.id,
                    fmt.rotulo,
                    fmt.fabricante,
                    fmt.extensao_tipica,
                    fmt.assinatura.hex() if fmt.assinatura else None,
                    fmt.binario,
                    # Derivado do registro, nunca escrito a mao: o banco so
                    # afirma leitor quando existe modulo registrado pra ele.
                    "nativo" if fmt.id in LEITORES else "ausente",
                    type(LEITORES[fmt.id]).__module__ if fmt.id in LEITORES else None,
                ),
            )
            resumo.formatos += 1

        for unidade, (gid, rotulo, dim) in UNIDADE_PARA_GRANDEZA.items():
            conn.execute(
                """insert into grandeza (id, rotulo, unidade_canonica, dimensao_si)
                   values (%s,%s,%s,%s) on conflict (id) do nothing""",
                (gid, rotulo, unidade, dim),
            )
            resumo.grandezas += 1

        # Canal canonico: um por nome distinto, com a unidade que TODOS os
        # perfis concordam (varredura de 29/08 nao achou nenhum conflito).
        unidade_do_canal: dict[str, str] = {}
        for canais in perfis.values():
            for canal, spec in canais.items():
                if spec.get("normalize_by_max"):
                    continue
                unidade_do_canal.setdefault(canal, spec["unit_out"])
        # O freio em pressao nasce aqui, e nao no aliases.yaml.
        unidade_do_canal["brake_press"] = "kPa"

        conn.execute(
            """insert into mapa_canal (versao, nota) values (%s,%s)
               on conflict (versao) do nothing""",
            (
                mapa_versao,
                (
                    "Carga inicial do aliases.yaml do saru-app (snapshot aa94872). "
                    "brake_press criado nesta versao: os 9 perfis de logger real "
                    "usavam normalizacao pelo maximo do arquivo, que quebra "
                    "comparacao entre arquivos."
                ),
            ),
        )

        for canal, unidade in sorted(unidade_do_canal.items()):
            gid = UNIDADE_PARA_GRANDEZA[unidade][0]
            canto, ponto = _decompor(canal)
            conn.execute(
                """insert into canal_canonico
                     (id, rotulo, grandeza_id, canto, ponto, dominio, obrigatorio)
                   values (%s,%s,%s,%s,%s,%s,%s)
                   on conflict (id) do nothing""",
                (canal, canal, gid, canto, ponto, "ambos", canal in ("speed", "time")),
            )
            resumo.canais += 1

        for perfil, canais in sorted(perfis.items()):
            formato = PERFIL_PARA_FORMATO.get(perfil)
            if formato is None:
                motivo = MOTIVO_PULADO.get(perfil, "sem formato medido no catalogo")
                resumo.pulados.append(f"{perfil}: {motivo}")
                continue
            conn.execute(
                """insert into perfil_origem (id, formato_id, rotulo, simulado)
                   values (%s,%s,%s,%s) on conflict (id) do nothing""",
                (perfil, formato, perfil, perfil in SIMULADOS),
            )
            resumo.perfis += 1

            for canal, spec in canais.items():
                colunas = spec["col"]
                colunas = colunas if isinstance(colunas, list) else [colunas]
                alvo, unidade_entrada, fator = canal, spec["unit_in"], spec.get("scale")
                if spec.get("normalize_by_max"):
                    alvo, fator = "brake_press", BAR_PARA_KPA
                    resumo.reescritos.append(f"{perfil}.{canal} -> brake_press")
                if fator is None:
                    fator = 1.0
                nota = (
                    "normalize_by_max do aliases.yaml descartado: o freio fica "
                    "em pressao, a normalizacao e da analise"
                    if spec.get("normalize_by_max")
                    else None
                )
                for coluna in colunas:
                    conn.execute(
                        """insert into mapeamento_canal
                             (perfil_id, coluna_bruta, mapa_versao,
                              canal_canonico_id, unidade_entrada, fator_escala,
                              "offset", nota)
                           values (%s,%s,%s,%s,%s,%s,%s,%s)
                           on conflict (perfil_id, coluna_bruta, mapa_versao)
                           do nothing""",
                        (
                            perfil,
                            coluna,
                            mapa_versao,
                            alvo,
                            unidade_entrada,
                            float(fator),
                            0.0,
                            nota,
                        ),
                    )
                    resumo.mapeamentos += 1
    return resumo
