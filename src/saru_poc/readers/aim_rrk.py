"""Leitor de inventario para AiM RS2, arquivo de run (`.rrk`), formato aim_rrk.

Estrutura MEDIDA em 2026-08-29 contra os 67 arquivos `.rrk` do acervo. Mesma
familia de container do `.gpk` (ver `aim_gpk.py`), so que menor: assinatura,
pseudo-registro e registro real tem a metade do tamanho.

Cada segmento comeca com a assinatura repetida duas vezes::

    'HEAD\\x00\\x01' (16 bytes, offset 0)
    'HEAD\\x00\\x01' (16 bytes, offset 16, identica a primeira)

seguida de 16 bytes de cabecalho nao decodificados (offset 32 a 47: um campo
ali parece contador em alguns arquivos e zero em outros, sem padrao estavel
o bastante pra virar contrato), e de um pseudo-registro fixo de 16 bytes no
offset 48: tag `NSOL` + contador u32 sempre igual a 256 + 8 bytes zero.
Depois, offset 64 em diante, a sequencia real de registros:

    tag 'NSOL' (4 bytes) + contador u32 (4 bytes) + payload (56 bytes)
    = 64 bytes por registro, fixo.

O contador sobe quase sempre de 40 em 40 (o dobro do passo do `.gpk`
irmao: se o contador do `.gpk` de fato for tempo em milissegundos, o `.rrk`
amostra na metade da taxa, ~25 Hz contra ~50 Hz. Isso e INFERENCIA, o
arquivo nao declara unidade em lugar nenhum: o contador cru vai pra `bruto`
sem traduzir.

**Multiplos segmentos, confirmado em uso real neste formato** (diferente do
`.gpk`, que nunca usou o recurso nos 68 arquivos medidos): 12 dos 67
CAMINHOS de `.rrk` do acervo tem mais de uma ocorrencia da assinatura dupla
`HEAD` dentro do mesmo arquivo fisico, cada uma abrindo um segmento com seu
proprio cabecalho (sao so 3 SESSOES distintas por conteudo, cada uma
salva em ate 4 pastas diferentes do acervo, ex. `superbike/Goiânia/` e
`porsche-cup/.../Goiânia/`: por isso 12 caminhos, nao 12 gravacoes
diferentes). Nos casos medidos, o ULTIMO segmento e um cabecalho sem
nenhum registro depois (0 bytes ate o fim do arquivo): contribui 0 pra
contagem de canal, e resultado legitimo, nao e truncamento nem erro.
Exemplo medido: `Fabio PittaBMW S1000RR18112022 (2022_12_18 20_23_00
UTC).rrk`, 205632 bytes, 3 segmentos em offset 0, 5696 e 205568 (o ultimo e
so o cabecalho de 64 bytes ate o fim do arquivo).

**O que NAO foi confirmado**: semantica do payload de 56 bytes. As mesmas
buscas descritas em `aim_gpk.py` (grau decimal contra o par `.xrk` de mesmo
radical, ECEF em metro/centimetro) nao foram refeitas campo a campo pro
`.rrk` porque o arquivo e pequeno demais (media 240 KB, contra os 71 MB
somados do acervo `.gpk`) pra caber amostra de canal completa por volta: a
suspeita de trabalho anterior (nao verificada aqui de novo) e de que
`.rrk` carrega indice ou resumo de volta, nao serie de canal amostrada.
Nenhuma tabela do banco de configuracao AiM (`Configs_20800CLI.mdb`,
`CONF_CANALELOGGER`) foi encontrada com uma chave que bata com o contador
ou com qualquer campo fixo deste registro: a hipotese do enunciado (canal
por indice numerico resolvido contra `CONF_CANALELOGGER`) NAO se confirmou
com o que este leitor consegue medir sem template de campo do payload.

Por isso `Cabecalho.canais = ()`. O inventario estrutural vai em `bruto`.

Arquivo maior do acervo: 1.06 MB (67 arquivos). Leitura inteira em memoria
segue o mesmo padrao de `xrk.py`, nao o de `ld.py` (arquivos de 400 MB+).
"""

from __future__ import annotations

import struct
from collections import Counter
from itertools import pairwise
from pathlib import Path

from .base import Cabecalho, ErroDeLeitura, LeitorDeInventario

_VERSAO = "0.1.0"

_ASSINATURA = b"HEAD\x00\x01"
_ASSINATURA_LEN = 6
_OFFSET_ASSINATURA_2 = 16
_OFFSET_PSEUDO_REGISTRO = 48
_TAG_PSEUDO_ESPERADA = b"NSOL"
_CTR_PSEUDO_ESPERADO = 256
_OFFSET_REGISTROS = 64
_TAG_REGISTRO = b"NSOL"
_TAMANHO_REGISTRO = 64


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
            f"{nome_arquivo}: assinatura aim_rrk ({_ASSINATURA!r}) ausente no offset 0"
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
        formato_id="aim_rrk",
        leitor_versao=_VERSAO,
        canais=(),
        capturado_em=None,
        duracao_s=None,
        venue_declarado=None,
        bruto=bruto,
    )


class LeitorAimRrk(LeitorDeInventario):
    formato_id = "aim_rrk"
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
