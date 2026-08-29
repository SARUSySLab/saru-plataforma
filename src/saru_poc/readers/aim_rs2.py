"""Leitor de inventario da familia AiM RaceStudio 2 (`.drk`, `.gpk`, `.rrk`).

So `.drk` e `.bak` tem leitor aqui (formato_id `aim_drk`, `.bak` como alias
de extensao do mesmo formato). `.gpk` (`aim_gpk`) e `.rrk` (`aim_rrk`) ficam
SEM leitor de proposito: a medicao (`docs/aim-rs2-medicao.md`) nao achou
estrutura decodificavel neles com confianca suficiente pra registrar leitor.
Ver o relatorio pra cada item da medicao.

O que este leitor entrega, medido contra os 129 arquivos `.drk`/`.bak` do
acervo em 2026-08-29:

1. **Canal com amostra: NAO.** A tabela de descritores de 288 bytes a partir
   do offset `0x800`, que e o que o leitor de referencia do saru-app
   (`drk_file.py`, so leitura) assume, nao decodifica NENHUM canal em
   NENHUM dos 129 arquivos (nem nos 67 `.rrk`, que passam pelo mesmo parser
   la). `Cabecalho.canais` sai sempre como tupla vazia, o mesmo padrao que
   `motec_ldx` ja usa pra sidecar sem canal.

2. **Metadado de sessao: SIM, pra 125 dos 129 arquivos (97%), exatamente os
   que tem magic `RDX\\x02`** (72 dos 76 `.drk` + 100% dos 53 `.bak`).
   Quatro campos de texto puro ASCII em offset FIXO e absoluto, medidos e
   confirmados em amostra aleatoria de 20 arquivos mais os 129 completos:

   - `0x4c` (24 bytes): data/hora de captura, formato `DD-MM-AA HH:MM:SS`.
   - `0x440` (40 bytes): veiculo.
   - `0x468` (40 bytes): pista/venue.
   - `0x490` (40 bytes): piloto.

   Os tres ultimos sao contiguos (`0x440+40=0x468`, `0x468+40=0x490`): e um
   array de 3 campos de 40 bytes, nao 3 offsets soltos.

   Os 4 arquivos sem esses campos (`Test.drk`, `Test #1.drk`, `WarmUp.drk`,
   `81214006.drk`) nao sao falha de leitura: sao a outra variante de magic
   (`RD\\x90\\x01` ou `RD\\xf4\\x01`, 4 dos 129 arquivos) e tem os 4 campos
   genuinamente vazios (string vazia, nao lixo binario). Cabecalho pobre e
   resultado legitimo aqui, do jeito que `.ldx` sem marcador ja trata.

Formula pra achar esses offsets: nenhuma. Foram medidos por busca de string
ASCII imprimivel nos primeiros 8 KB de arquivos reais, cruzando contra o
nome do arquivo e o `session_name`/`venue` que `drk_file.py` extraia por
heuristica (primeira/segunda string "limpa"). Aqui a extracao e por offset
fixo, testada contra os 129 arquivos, nao por heuristica de posicao
relativa.
"""

from __future__ import annotations

import re
from pathlib import Path

from .base import Cabecalho, ErroDeLeitura, LeitorDeInventario

# Offsets medidos contra o acervo (ver docstring do modulo e
# docs/aim-rs2-medicao.md). Absolutos desde o inicio do arquivo, nao
# relativos a nenhum ponteiro do cabecalho.
_OFF_DATA_HORA = 0x4C
_LEN_DATA_HORA = 24

_OFF_VEICULO = 0x440
_OFF_VENUE = 0x468
_OFF_PILOTO = 0x490
_LEN_CAMPO = 40  # os tres campos acima sao contiguos, mesmo tamanho.

# Precisa caber ate o fim do campo piloto pra inspecionar ter algo pra ler.
_TAMANHO_MINIMO = _OFF_PILOTO + _LEN_CAMPO

# Um campo de metadado real e ASCII imprimivel puro (0x20-0x7e) ou vazio.
# Byte fora dessa faixa e prova de que o offset caiu em dado binario (a
# variante de magic errada, ou um campo que este leitor nao mapeou), nao
# texto: dai o campo vira None em vez de string lixo.
_ASCII_IMPRIMIVEL = re.compile(rb"^[\x20-\x7e]*$")

# Data no formato `DD-MM-AA HH:MM:SS`, ano com 2 digitos.
_RE_DATA_HORA = re.compile(r"^(\d{2})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})$")


def _ler_campo_texto(bruto_arquivo: bytes, offset: int, tamanho: int) -> str | None:
    """Le um campo de `tamanho` bytes em `offset`, corta no primeiro nulo.

    Devolve `None` quando o campo tem byte fora do intervalo ASCII
    imprimivel: nesse caso o offset nao caiu em texto (variante de arquivo
    diferente, ou o campo realmente nao existe ali), e inventar string a
    partir de lixo binario e exatamente o erro que o leitor de referencia
    cometia (nomes de canal como `'°'` ou `'y'`).
    """
    fim = offset + tamanho
    if fim > len(bruto_arquivo):
        return None
    chunk = bruto_arquivo[offset:fim]
    ate_o_nulo = chunk.split(b"\x00", 1)[0]
    if not _ASCII_IMPRIMIVEL.match(ate_o_nulo):
        return None
    return ate_o_nulo.decode("ascii").strip()


def _normalizar_data_hora(bruto: str | None) -> tuple[str | None, str]:
    """Converte `DD-MM-AA HH:MM:SS` pra ISO 8601. Ano de 2 digitos: assume
    seculo 20xx (todo o acervo medido cai entre 2018 e 2022; nao ha arquivo
    com ano que sugira 19xx). Marca `(inferido)` no nome do campo de
    procedencia pra quem consumir saber que o seculo foi assumido, nao lido.

    Sem match no formato esperado, devolve `None` e preserva a string crua:
    nunca inventa data.
    """
    bruto_str = bruto or ""
    if not bruto:
        return None, bruto_str
    m = _RE_DATA_HORA.match(bruto)
    if not m:
        return None, bruto_str
    dia, mes, ano2, hora, minuto, segundo = m.groups()
    ano = 2000 + int(ano2)
    iso = f"{ano:04d}-{mes}-{dia}T{hora}:{minuto}:{segundo}"
    return iso, bruto_str


# --- tabela de voltas ------------------------------------------------------
#
# O `.drk` e o INDICE da familia RS2, e o indice carrega uma tabela de voltas:
# registros de 288 bytes, contador de volta (int32, comeca em 0) no rel +0,
# tempo ACUMULADO desde o primeiro beacon (int32, ms) no rel +272 e DURACAO da
# volta (int32, ms) no rel +276. Medido em 29/08 contra os 128 `.drk`/`.bak`
# do acervo, validado contra os beacons do `.xrk` irmao: as duracoes batem
# byte a byte, EXCETO a do ultimo registro, que fecha no DESLIGAMENTO do
# logger e nao num beacon (sempre alguns decimos/segundos a mais que o `.xrk`;
# no caso extremo, um kart com transponder falhando fechou 500 s de sessao num
# "registro de volta" so). Por isso o que sai daqui sao as PASSAGENS
# confirmadas: o inicio de cada registro e um beacon real, o fim do ultimo
# nao e, entao N registros rendem N-1 voltas e a ultima fica de fora COM
# MOTIVO, mesma filosofia do out-lap/in-lap do corte.
#
# O relogio e RELATIVO ao primeiro beacon (acumulado do registro 0 e sempre
# zero), nao ao inicio da gravacao. Num bundle com `.xrk` isso nao importa:
# o degrau do `.xrk` vem antes na cascata e tem o relogio das series. O degrau
# do `.drk` so decide quando o arquivo esta sozinho, e sozinho nao ha serie
# com que desalinhar.

_REG_VOLTA_BYTES = 288
_REG_REL_ACUMULADO = 272
_REG_REL_DURACAO = 276
# Duracao plausivel de volta: mesmo espirito do MIN_VOLTA_S do corte, com
# teto largo (1h) so pra descartar lixo binario que casaria por acaso.
_DURACAO_MIN_MS = 10_000
_DURACAO_MAX_MS = 3_600_000


def _tabela_de_voltas(dados: bytes) -> list[tuple[int, int]]:
    """(acumulado_ms, duracao_ms) de cada registro da tabela, ou lista vazia.

    A tabela nao tem offset fixo entre arquivos (medido: varia com o tamanho
    da regiao de configuracao), entao o inicio e achado por ASSINATURA: um
    registro com contador 0, acumulado 0 e duracao plausivel, seguido de um
    registro com contador 1 cujo acumulado e exatamente a duracao do
    primeiro. Dois registros encadeados assim por acaso, em lixo binario,
    nao foram medidos em nenhum dos 128 arquivos. A caminhada para no
    primeiro registro que quebra o encadeamento (contador fora de sequencia,
    acumulado que nao soma, duracao implausivel): tabela parcial e resultado,
    nao erro.
    """
    tamanho = len(dados)

    def _i32(off: int) -> int:
        return int.from_bytes(dados[off : off + 4], "little", signed=True)

    for off in range(0, tamanho - 2 * _REG_VOLTA_BYTES, 4):
        if _i32(off) != 0 or _i32(off + _REG_REL_ACUMULADO) != 0:
            continue
        dur0 = _i32(off + _REG_REL_DURACAO)
        if not (_DURACAO_MIN_MS <= dur0 <= _DURACAO_MAX_MS):
            continue
        if _i32(off + _REG_VOLTA_BYTES) != 1 or _i32(
            off + _REG_VOLTA_BYTES + _REG_REL_ACUMULADO
        ) != dur0:
            continue
        registros = [(0, dur0)]
        k = 1
        while off + k * _REG_VOLTA_BYTES + _REG_REL_DURACAO + 4 <= tamanho:
            base = off + k * _REG_VOLTA_BYTES
            acumulado = _i32(base + _REG_REL_ACUMULADO)
            duracao = _i32(base + _REG_REL_DURACAO)
            if (
                _i32(base) != k
                or acumulado != registros[-1][0] + registros[-1][1]
                or not (_DURACAO_MIN_MS <= duracao <= _DURACAO_MAX_MS)
            ):
                break
            registros.append((acumulado, duracao))
            k += 1
        return registros
    return []


class LeitorAimDrk(LeitorDeInventario):
    """Inventario de metadado do container AiM RS2 `.drk`/`.bak`.

    Nao le canal: a tabela de descritores de 288 bytes que o leitor de
    referencia do saru-app assume nao decodifica em nenhum arquivo medido
    (ver docstring do modulo). `canais` sai sempre como tupla vazia. Desde
    29/08 le a TABELA DE VOLTAS do indice (ver bloco acima): e o que permite
    cortar volta de um `.drk` enviado sozinho.
    """

    formato_id = "aim_drk"
    versao = "2"

    def inspecionar(self, caminho: Path) -> Cabecalho:
        tamanho_arquivo = caminho.stat().st_size
        if tamanho_arquivo < _TAMANHO_MINIMO:
            raise ErroDeLeitura(
                f"{caminho}: arquivo menor que a regiao de metadado medida "
                f"({tamanho_arquivo} bytes, esperava >= {_TAMANHO_MINIMO}) "
                f"em offset {_OFF_PILOTO}"
            )

        # Arquivo inteiro, e nao so a regiao de metadado: a tabela de voltas
        # nao tem offset fixo (ver `_tabela_de_voltas`) e o maior `.drk` do
        # acervo tem 1,8 MB, barato de varrer.
        dados = caminho.read_bytes()
        cabecalho_bruto = dados[:_TAMANHO_MINIMO]

        if len(cabecalho_bruto) < _TAMANHO_MINIMO:
            raise ErroDeLeitura(
                f"{caminho}: EOF lendo regiao de metadado "
                f"({len(cabecalho_bruto)}/{_TAMANHO_MINIMO} bytes)"
            )

        data_hora_bruta = _ler_campo_texto(
            cabecalho_bruto, _OFF_DATA_HORA, _LEN_DATA_HORA
        )
        veiculo = _ler_campo_texto(cabecalho_bruto, _OFF_VEICULO, _LEN_CAMPO)
        venue = _ler_campo_texto(cabecalho_bruto, _OFF_VENUE, _LEN_CAMPO)
        piloto = _ler_campo_texto(cabecalho_bruto, _OFF_PILOTO, _LEN_CAMPO)

        capturado_em, capturado_em_bruto = _normalizar_data_hora(data_hora_bruta)

        bruto: dict[str, str] = {
            "piloto": piloto or "",
            "veiculo": veiculo or "",
            "capturado_em_bruto": capturado_em_bruto,
        }
        if capturado_em is not None:
            bruto["capturado_em_seculo"] = "inferido (20xx, ano de 2 digitos)"

        registros = _tabela_de_voltas(dados)
        if len(registros) >= 2:
            # Passagens confirmadas por beacon: o INICIO de cada registro.
            # O fim do ultimo registro fica de fora de proposito (fecha no
            # desligamento do logger, nao num beacon; ver bloco da tabela).
            passagens = [acumulado for acumulado, _duracao in registros]
            bruto["lap_beacons_ms"] = ",".join(str(v) for v in passagens)
            bruto["lap_registros"] = str(len(registros))
            bruto["lap_ultimo_descartado"] = (
                "o ultimo registro fecha no desligamento do logger, nao no "
                f"beacon ({registros[-1][1]} ms): nao vira volta"
            )
        return Cabecalho(
            formato_id=self.formato_id,
            leitor_versao=self.versao,
            canais=(),
            capturado_em=capturado_em,
            duracao_s=None,
            venue_declarado=venue or None,
            bruto=bruto,
        )
