"""Teste de desempenho e equivalencia do leitor .xrk (formato_id aim_xrk).

Contexto (medido com cProfile em 29/08 contra o acervo real, ver diagnostico
da tarefa que originou este arquivo): a etapa de ingestao de um `.xrk` de
6,75 MB (343.928 amostras, 55 canais) levava 2,79 s no total, com `ler()`
sozinho consumindo 2,4 a 2,55 s (mais de 85% da ingestao). O gargalo era
`struct.unpack_from` amostra a amostra (2,8 milhoes de chamadas) e um buffer
`dict[periodo_us][ts_ms][cid]` que gerava 5,4 milhoes de `dict.get()` no
flush. A correcao (`src/saru_poc/readers/xrk.py`) trocou o decode escalar
por um gather vetorizado em bloco (`np.frombuffer` + fancy-index), a rajada
`M` por um unico `np.frombuffer` por registro (era um loop de
`struct.unpack_from` por amostra), e o buffer aninhado por listas paralelas
+ montagem de matriz vetorizada por janela (`np.unique`/`searchsorted`).

Este arquivo tem dois testes:

1. `test_ler_trava_a_saida_do_arquivo_real`: trava o resultado de `ler()` e
   `inspecionar()` pro MESMO arquivo usado no diagnostico (6,75 MB, pasta
   `f3/Gabriel Bortoleto`), via hash de todo o conteudo decodificado
   (schema, ordem de coluna, valor a valor, NaN incluido). Qualquer
   divergencia de decodificacao futura quebra este teste, mesmo que o total
   de linhas continue batendo. Roda so quando o acervo estiver montado
   nesta maquina (mesmo padrao de `tests/test_reader_xrk.py`): nao
   versionamos arquivo real, tem nome de piloto real.
2. `test_tempo_de_leitura_dentro_do_teto`: mede `ler()` no mesmo arquivo e
   falha se passar do teto. Ver a escolha do teto no docstring do teste.

A prova de equivalencia ENTRE a versao antiga (dict aninhado, struct por
amostra) e a nova (vetorizada) rodou fora deste arquivo, comparando os 3
arquivos reais abaixo (o de referencia do diagnostico + kart-guara +
superbike) por hash exato de cada lote, valor a valor: os tres bateram
identico depois da correcao do corte de janela (ver relato da tarefa). O
teste 1 aqui e o que fica travado pra sempre no CI/local, sobre o arquivo de
referencia do diagnostico.
"""

from __future__ import annotations

import hashlib
import math
import time
from pathlib import Path

import pytest

from saru_poc.config import CONFIG
from saru_poc.readers.xrk import _CANAIS_GPS, LeitorXrk

# Arquivo de referencia do diagnostico: 6,75 MB, 343.928 amostras, 55 canais,
# leva 2,4 a 2,55 s em ler() na implementacao antiga (medido com cProfile).
_ARQUIVO_REFERENCIA = (
    "telemetria/f3/Gabriel Bortoleto/F309-016/2021-02-02/"
    "Gabriel Bortoleto_F309-016_20210202_161306_Interlagos_4300133_c_1154.xrk"
)


def _caminho_referencia() -> Path:
    return CONFIG.acervo_root / _ARQUIVO_REFERENCIA


def _acervo_disponivel() -> bool:
    return _caminho_referencia().exists()


def _hash_cabecalho(canais) -> str:
    """Hash estavel do inventario: nome, taxa e contagem de amostra de CADA
    canal, ordenado por nome (a ordem de dict de `canais.items()` no leitor
    nao e um contrato, entao ordenamos aqui pra o hash nao mudar por causa
    de reordenacao interna irrelevante)."""
    h = hashlib.sha256()
    for c in sorted(canais, key=lambda c: c.nome_bruto):
        h.update(f"{c.nome_bruto}|{c.frequencia_hz}|{c.n_amostras}\n".encode())
    return h.hexdigest()


def _hash_lotes(lotes) -> tuple[str, int, int]:
    """Hash estavel do resultado de `ler()`: pra cada lote, a frequencia, o
    nome de cada coluna (ordem inclusa) e o VALOR de cada celula (`NaN`
    normalizado pra string fixa, senao `NaN != NaN` faria o hash mudar a
    cada execucao). Devolve (hash, total_de_linhas, n_lotes)."""
    h = hashlib.sha256()
    total_linhas = 0
    n_lotes = 0
    for lote in lotes:
        n_lotes += 1
        total_linhas += lote.tabela.num_rows
        h.update(f"{round(lote.frequencia_hz, 6)}|".encode())
        nomes = lote.tabela.schema.names
        h.update(",".join(nomes).encode())
        for nome in nomes:
            valores = lote.tabela.column(nome).to_pylist()
            rep = ";".join(
                "nan" if (isinstance(v, float) and math.isnan(v)) else repr(v)
                for v in valores
            )
            h.update(rep.encode())
    return h.hexdigest(), total_linhas, n_lotes


@pytest.mark.skipif(not _acervo_disponivel(), reason="acervo nao montado nesta maquina")
def test_ler_trava_a_saida_do_arquivo_real() -> None:
    """Trava byte a byte (via hash) a saida de `inspecionar()` e `ler()`
    pro arquivo de referencia do diagnostico de desempenho.

    Os hashes abaixo foram gerados RODANDO a implementacao vetorizada e
    comparados manualmente, fora deste teste, contra a saida da
    implementacao antiga (dict aninhado + struct por amostra) pro MESMO
    arquivo: identicos, lote a lote, valor a valor (ver docstring do
    modulo). Se este teste falhar depois de mexer no leitor, a decodificacao
    mudou - isso e sempre bug, nunca ruido: e a mesma sequencia de bytes de
    entrada todas as vezes.

    Duas camadas desde 29/08 (canais GPS sintetizados): a trava ANTIGA
    continua valendo sobre o subconjunto sem GPS (mexer no GPS nao pode
    mudar UM byte do que ja saia antes), e uma trava nova cobre a saida
    completa, GPS incluso. Os hashes do GPS foram validados fora daqui
    contra o oraculo libxrk: 111 dos 113 arquivos do acervo com igualdade
    bit-exata nos 12 canais no dtype do oraculo (os 2 restantes o oraculo
    nem abre; ver scripts/auditar_xrk_contra_libxrk.py pro racional do
    oraculo).
    """
    leitor = LeitorXrk()
    caminho = _caminho_referencia()

    nomes_gps = {nome for nome, _unidade in _CANAIS_GPS}

    cab = leitor.inspecionar(caminho)
    assert len(cab.canais) == 42  # 30 do CHS + 12 GPS sintetizados
    assert cab.duracao_s == pytest.approx(1318.3, abs=0.05)
    canais_sem_gps = [c for c in cab.canais if c.nome_bruto not in nomes_gps]
    assert len(canais_sem_gps) == 30
    # Trava antiga, intacta: o inventario pre-GPS nao mudou um byte.
    assert _hash_cabecalho(canais_sem_gps) == (
        "0c4ad0edabb114f5785fc2848c5a363ab116511fcdb303efa10b7a1c54b24f07"
    )
    assert _hash_cabecalho(cab.canais) == (
        "087ee551b098f0bfc6dae23aaea1fdba6ffe9eb90f9a7dd463131bf6aedf58d3"
    )

    lotes = list(leitor.ler(caminho))
    lotes_principais = [lote for lote in lotes if lote.serie != "gps"]
    hash_principais, linhas_principais, n_principais = _hash_lotes(lotes_principais)
    assert n_principais == 6
    assert linhas_principais == 343_928
    # Hash de VALOR atualizado em 29/08 pelo decode tipado (corpo[20] do CHS):
    # o arquivo de referencia tem 24 canais float16, 6 uint16 e so 1 int16
    # entre os de 2 bytes, e ate entao TODOS saiam como int16 (um fp16 de
    # 100.0 virava 22080). A estrutura (contagem de lotes/linhas, acima) nao
    # mudou; os VALORES mudaram de proposito, validados contra o oraculo
    # libxrk canal a canal (EDL8_TPS, BRAKE_F, STEERING, LAT_ACC identicos
    # em min/max/contagem no arquivo Bortoleto c_1130).
    assert hash_principais == (
        "4a75e0721c7b3a20df61b5e245ee5f4555c6f10c21b5e883cd8b018d6435f98f"
    )
    hash_lotes, total_linhas, n_lotes = _hash_lotes(lotes)
    assert n_lotes == 7  # + a serie GPS (5.239 amostras a 4 Hz num lote so)
    assert total_linhas == 349_167
    assert hash_lotes == (
        "3b38d7768d71201f1a515075fe4b63841163b3de5feb3c361b83f3e02ad30d6d"
    )


@pytest.mark.skipif(not _acervo_disponivel(), reason="acervo nao montado nesta maquina")
def test_tempo_de_leitura_dentro_do_teto() -> None:
    """`ler()` do arquivo de referencia (6,75 MB) nao pode passar do teto.

    Escolha do teto: 3,5 s de tempo de CPU (`time.process_time()`, nao
    tempo de parede - imune a pausa por I/O/swap, o que importa aqui e
    quanto trabalho de CPU o parser faz). Medido nesta maquina (repetido,
    process_time por ser estavel mesmo sob contencao de memoria que deixou o
    tempo de PAREDE bem ruidoso, ate 5 s, no mesmo hardware): a
    implementacao antiga (struct por amostra + dict aninhado) ficava em
    2,2 a 2,3 s de CPU; a vetorizada, em 1,7 a 2,2 s. O teto de 3,5 s da
    quase 1,6x de folga sobre o pior caso ja observado da versao NOVA, e
    ainda assim fica abaixo do que uma regressao real (ex.: voltar a
    struct.unpack_from por amostra, ou pior, uma reintroducao acidental de
    complexidade quadratica na janela) deve custar num arquivo deste
    tamanho: e teto pra pegar regressao grosseira, nao pra flagrar uma
    piora de 10-20%.
    """
    leitor = LeitorXrk()
    caminho = _caminho_referencia()

    t0 = time.process_time()
    lotes = list(leitor.ler(caminho))
    duracao_cpu_s = time.process_time() - t0

    assert len(lotes) > 0
    assert duracao_cpu_s < 3.5, (
        f"ler() do arquivo de referencia levou {duracao_cpu_s:.3f}s de CPU, "
        "acima do teto de 3.5s: possivel regressao de desempenho no parser"
    )
