"""Leitor de inventario para AiM RS2, sidecar de GPS (`.gpk`), formato aim_gpk.

Estrutura MEDIDA em 2026-08-29 contra os 68 arquivos `.gpk` do acervo (nenhuma
veio de documentacao do fabricante, que nao e publica para este formato).

O arquivo e uma sequencia de UM OU MAIS "segmentos" concatenados. Cada
segmento comeca com a assinatura repetida duas vezes::

    'PROV\\x00\\x01' (16 bytes, offset 0)
    'PROV\\x00\\x01' (16 bytes, offset 16, identica a primeira)

seguida de 48 bytes de cabecalho nao decodificados aqui (offset 32 a 79: nos
68 arquivos medidos carregam so lixo binario de baixa entropia quando lidos
como float64, nenhum campo bateu com nada verificavel), e de um
"pseudo-registro" de 16 bytes fixo em offset 80: tag `PSOL` + contador u32
sempre igual a 256 + 8 bytes zero. Depois disso, offset 96 em diante, vem a
sequencia real de registros:

    tag 'PSOL' (4 bytes) + contador u32 (4 bytes) + payload (136 bytes)
    = 144 bytes por registro, fixo.

O contador sobe quase sempre de 20 em 20 entre registros consecutivos (medido
22321 de 22323 passos no arquivo de referencia, os outros 2 sobem 19): e
candidato forte a timestamp em milissegundos e taxa de ~50 Hz, mas isso e
INFERENCIA, nao esta declarado em lugar nenhum do arquivo. Este leitor nao
afirma unidade nem taxa: guarda o contador cru em `bruto`.

Em 68/68 arquivos do acervo, o numero de bytes depois do offset 96 (ou do
inicio do proximo segmento, quando existe mais de um) divide exatamente por
144: e a evidencia de que o framing acima esta correto, medida arquivo por
arquivo, nao amostrada.

**Multiplos segmentos**: 3 dos 67 arquivos (na verdade, `.rrk`, ver
`aim_rrk.py`; nenhum `.gpk` do acervo repetiu a assinatura `PROV` mais de uma
vez) tem mais de uma ocorrencia da assinatura dupla dentro do mesmo arquivo,
cada uma abrindo um novo segmento com seu proprio cabecalho e sua propria
sequencia de registros (as vezes um segmento final SEM nenhum registro, so o
cabecalho: contribui 0 para a contagem de canal, e legitimo, nao e erro). O
leitor deste modulo trata `.gpk` da mesma forma por simetria e porque nada no
formato impede, ainda que nenhum `.gpk` medido tenha usado o recurso.

**O que NAO foi confirmado, e por isso NAO esta no contrato**: se os 136
bytes de payload de cada registro carregam coordenada GPS. Tentativas
(todas negativas) contra o par `.xrk` de mesmo radical de nome
(`davi_67_A.Senna Kart_a_0277`, que tem GPS ECEF valido, decodificado e
geoconvertido para lat -15.83 / lon -47.97, Guara/Brasilia, altitude ~1081 m,
batendo com o nome da pasta `kart-guara`):

- os 17 primeiros float64 do payload como grau decimal de lat/lon: nenhum
  par consistente na faixa esperada (~-15.8/-47.9) apareceu com offset fixo
  entre registros: a busca por qualquer float64 no arquivo inteiro perto de
  -15.8257 (tolerancia de 0.01 grau, ~1 km) achou 25 ocorrencias soltas sem
  contrapartida de longitude no mesmo registro;
- ECEF em metros (float64) e em centimetros (int32), nas duas ordens
  x/y/z, com o valor esperado (~4.11e6, -4.56e6, -1.73e6 m): zero
  ocorrencias com tolerancia de 5 km;
- os dois primeiros float64 do payload (indices medidos como "velocidade" e
  "rumo" possiveis, por decrescerem/crescerem suavemente entre registros
  vizinhos) tem faixa de -46.9 a 133.7 no arquivo de referencia: grande
  demais pra grau de latitude/longitude de uma pista, mas plausivel pra
  velocidade (m/s) e rumo (graus). Fica como HIPOTESE NAO CONFIRMADA, nao
  suporta canal.

Por isso este leitor devolve `Cabecalho.canais = ()`: nao ha campo do
payload com semantica de canal validada contra a amostra real. E resultado
legitimo (mesmo padrao do `.ldx` deste repo). O inventario estrutural
(numero de registros, segmentos, contador) vai em `bruto`.

Arquivo maior do acervo: 4.78 MB (68 arquivos). Bem abaixo do teto que
motivou leitura via `seek` em `ld.py` (arquivos de 400 MB+): ler o arquivo
inteiro pra memoria aqui segue o mesmo padrao de `xrk.py` (arquivos ate 2 MB
no acervo dele), nao o de `ld.py`.
"""

from __future__ import annotations

import struct
from collections import Counter
from itertools import pairwise
from pathlib import Path

from .base import Cabecalho, ErroDeLeitura, LeitorDeInventario

_VERSAO = "0.1.0"

_ASSINATURA = b"PROV\x00\x01"
_ASSINATURA_LEN = 6
_OFFSET_ASSINATURA_2 = 16
_OFFSET_PSEUDO_REGISTRO = 80
_TAG_PSEUDO_ESPERADA = b"PSOL"
_CTR_PSEUDO_ESPERADO = 256
_OFFSET_REGISTROS = 96
_TAG_REGISTRO = b"PSOL"
_TAMANHO_REGISTRO = 144


def _segmentos(dados: bytes) -> list[int]:
    """Acha todos os inicios de segmento (assinatura dupla) no arquivo."""
    inicios = []
    idx = 0
    while True:
        idx = dados.find(_ASSINATURA, idx)
        if idx == -1:
            break
        if dados[idx + _OFFSET_ASSINATURA_2 : idx + _OFFSET_ASSINATURA_2 + 6] == (
            _ASSINATURA
        ):
            inicios.append(idx)
        idx += 1
    return inicios


def _inspecionar_bytes(dados: bytes, nome_arquivo: str) -> Cabecalho:
    tamanho_total = len(dados)
    if tamanho_total < _ASSINATURA_LEN or dados[:_ASSINATURA_LEN] != _ASSINATURA:
        raise ErroDeLeitura(
            f"{nome_arquivo}: assinatura aim_gpk ({_ASSINATURA!r}) ausente no offset 0"
        )

    inicios = _segmentos(dados)
    if not inicios or inicios[0] != 0:
        raise ErroDeLeitura(
            f"{nome_arquivo}: assinatura dupla de abertura de segmento nao "
            "confirmada no offset 0..21"
        )

    total_registros = 0
    contadores: list[int] = []
    tamanhos_segmento: list[int] = []
    for i, inicio in enumerate(inicios):
        fim_segmento = inicios[i + 1] if i + 1 < len(inicios) else tamanho_total
        off_pseudo = inicio + _OFFSET_PSEUDO_REGISTRO
        if dados[off_pseudo : off_pseudo + 4] != _TAG_PSEUDO_ESPERADA:
            raise ErroDeLeitura(
                f"{nome_arquivo}: pseudo-registro '{_TAG_PSEUDO_ESPERADA.decode()}' "
                f"ausente no offset {off_pseudo}"
            )
        ctr_pseudo = struct.unpack_from("<I", dados, off_pseudo + 4)[0]
        if ctr_pseudo != _CTR_PSEUDO_ESPERADO:
            raise ErroDeLeitura(
                f"{nome_arquivo}: pseudo-registro no offset {off_pseudo} tem "
                f"contador {ctr_pseudo}, esperado {_CTR_PSEUDO_ESPERADO} "
                "(constante medida no acervo)"
            )
        inicio_registros = inicio + _OFFSET_REGISTROS
        restante = fim_segmento - inicio_registros
        if restante < 0 or restante % _TAMANHO_REGISTRO != 0:
            raise ErroDeLeitura(
                f"{nome_arquivo}: segmento em {inicio} tem {restante} bytes de "
                f"registro a partir do offset {inicio_registros}, nao e "
                f"multiplo de {_TAMANHO_REGISTRO} (registro de tamanho fixo)"
            )
        n_registros = restante // _TAMANHO_REGISTRO
        for r in range(n_registros):
            off = inicio_registros + r * _TAMANHO_REGISTRO
            if dados[off : off + 4] != _TAG_REGISTRO:
                raise ErroDeLeitura(
                    f"{nome_arquivo}: registro esperado '"
                    f"{_TAG_REGISTRO.decode()}' ausente no offset {off}"
                )
            contadores.append(struct.unpack_from("<I", dados, off + 4)[0])
        total_registros += n_registros
        tamanhos_segmento.append(n_registros)

    bruto: dict[str, str] = {
        "n_segmentos": str(len(inicios)),
        "n_registros_total": str(total_registros),
        "tamanho_registro_bytes": str(_TAMANHO_REGISTRO),
        "registros_por_segmento": ",".join(str(n) for n in tamanhos_segmento),
        "offsets_segmento": ",".join(str(o) for o in inicios),
        "semantica_payload": "nao confirmada (ver docstring do modulo)",
    }
    if contadores:
        bruto["contador_min"] = str(min(contadores))
        bruto["contador_max"] = str(max(contadores))
        diffs = Counter(b - a for a, b in pairwise(contadores))
        passo_dominante, _ = diffs.most_common(1)[0]
        bruto["passo_contador_dominante"] = str(passo_dominante)

    return Cabecalho(
        formato_id="aim_gpk",
        leitor_versao=_VERSAO,
        canais=(),
        capturado_em=None,
        duracao_s=None,
        venue_declarado=None,
        bruto=bruto,
    )


class LeitorAimGpk(LeitorDeInventario):
    formato_id = "aim_gpk"
    versao = _VERSAO
    suporta_amostra = False

    def inspecionar(self, caminho: Path) -> Cabecalho:
        try:
            dados = caminho.read_bytes()
        except OSError as exc:
            raise ErroDeLeitura(
                f"{caminho}: nao foi possivel ler o arquivo: {exc}"
            ) from exc
        if not dados:
            raise ErroDeLeitura(f"{caminho}: arquivo vazio")
        return _inspecionar_bytes(dados, str(caminho))
