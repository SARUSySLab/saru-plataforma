"""Leitor de inventario do container Pi Toolbox `.pds`, formato `pi_pds`.

MEDIDO do zero (nao ha porte de codigo do saru-app pra este formato: nunca
existiu leitor de `.pds` la). Tudo abaixo foi obtido por hexdump anotado e
diferenca binaria entre registros de canais reais do acervo (47 arquivos,
2026-08-29), nao por documentacao do fabricante (Pi Research/Cosworth nunca
publicou o layout).

ASSINATURA: os 4 primeiros bytes do arquivo variam entre 8 formas medidas
(`01 00 00 00`, `01 00 36 00`, `01 00 70 00`, `01 00 71 00`, `01 00 78 00`,
`01 07 01 00`, `01 43 3a 5c`, `01 74 65 6c`) e NAO sao usados aqui como
magic: sao os primeiros bytes de um campo de comprimento+conteudo que, nos
arquivos maiores, guarda um fragmento de caminho Windows (`C:\\...`) ou
texto (`tel...`) do posto de trabalho que gravou o arquivo, e nos arquivos
pequenos fica zerado. O que e establel nos 47 arquivos e o magic real, 4
bytes no offset 4: `1a 12 40 f7`, seguido por 16 bytes constantes (um GUID,
nao verificado aqui: bastam os 4 bytes do magic pra identificar o formato,
igual ao offset 0 dos outros leitores Pi).

ESTRUTURA MEDIDA (arquivo grava do fim pro comeco, tipico de formato Pi
Toolbox): o corpo do arquivo comeca com um cabecalho fixo, segue com a
amostra em blocos de `float64` (nunca lida por este leitor), e termina com
dois blocos de metadado que ficam SEMPRE nos ultimos bytes do arquivo,
independente do tamanho total (medido: 96 KB a 97 MB, a mesma distancia do
fim):

1. **Dicionario de canais**: lista de registros de tamanho fixo, EM ORDEM
   ALFABETICA pelo nome do canal. Neste leitor so o layout de 552 bytes por
   registro foi decifrado e validado (ver `_ESTRIDE_DICIONARIO`): nome em
   UTF-16LE no offset 0 do registro, o MESMO nome repetido no offset 88
   (usado aqui como assinatura de validacao, nao dado util), a unidade em
   UTF-16LE no offset 152, e o indice do canal (inteiro, mesma base do
   indice da tabela abaixo) nos ultimos 4 bytes do registro (offset 544).
   Ha um segundo layout, de 552... na verdade 304 bytes por registro, visto
   nos 10 arquivos de `workbooks/pi-toolbox-bootcamp/`: layout DIFERENTE
   (sem o nome duplicado em +88, unidade em offset diferente, e SEM campo de
   indice identificavel dentro do registro). Esse segundo layout NAO e
   suportado aqui: ver `docs/pi-pds-medicao.md` para os offsets medidos e o
   que falta pra decidir a leitura dele.

2. **Tabela de blocos de amostra**: logo apos o dicionario, uma lista de
   registros de 64 bytes, um por BLOCO de amostra. Nos arquivos pequenos
   (F3, 47 arquivos de 2026-08-29) ha um bloco por canal e a tabela vem em
   ordem de indice. No `REF 992.pds` do 992.1 (105,8 MB, medido em
   2026-09-14, ver `docs/pi-pds-medicao.md`) ha 4311 blocos pra 2937
   canais: um canal pode ter varios blocos (ate 71), a tabela NAO vem em
   ordem de indice e os offsets de amostra nao sao monotonicos. Campos
   medidos (todos `<i` de 4 bytes, offsets relativos ao inicio do registro):
   - offset 0: indice do canal (0-based, mesmo espaco do offset 544 do
     dicionario).
   - offset 16: intervalo entre amostras, em unidades de 1e-7 s (100 ns).
     `frequencia_hz = 1e7 / intervalo`. Validado contra os 7 valores que
     aparecem no acervo (100, 50, 25, 20, 10, 5 e 1 Hz), todos frequencias
     de log padrao de telemetria automotiva.
   - offset 20: numero de amostras do bloco.
   - offset 48: offset (em bytes, a partir do inicio do arquivo) de onde
     comecam as amostras deste bloco. NAO lido por este leitor (inventario,
     nao amostra), mas serve de invariante, ver abaixo.
   - offset 56: numero de serie do registro. Nos arquivos F3 vale
     `indice + 1`; no 992.1 e uma permutacao de 0 a 4310, sem relacao com o
     indice. Nao serve de checksum.
   - offset 60: nos arquivos F3 vale `indice + 1`; no 992.1 vale isso em
     2393 dos 4311 registros e outra coisa nos demais (significado nao
     medido). Nao serve de checksum.
   Um registro e valido quando intervalo e numero de amostras sao positivos,
   o indice cabe no dicionario e o bloco de amostra termina antes do
   dicionario. O primeiro registro invalido encerra a tabela (medido: no
   992.1 e no F3 o registro seguinte ao ultimo valido e lixo com intervalo
   zero).

   Tamanho da amostra: 8 bytes (`float64`) nos arquivos F3; no 992.1, 4
   bytes em 1328 canais, 1 byte em 918 e 2 bytes em 236 (canais discretos).
   Nenhum campo isolado do registro de dicionario ou da tabela determina o
   tamanho (varrido byte a byte e em u16 e u32, 2026-09-14). Por isso o
   tamanho e DEDUZIDO da propria tabela: com os blocos em ordem de offset, a
   distancia entre blocos consecutivos dividida pelo numero de amostras do
   primeiro tem que dar 1, 2, 4 ou 8. Essa e a invariante deste leitor:
   nenhum par pode se sobrepor (distancia menor que o numero de amostras), e
   pelo menos `_FRACAO_MINIMA_PARES_FECHADOS` dos pares tem que fechar
   exato. Medido: 45 de 45 pares no F3; 4308 de 4310 no 992.1, os dois
   restantes sao buracos (padding entre segmentos), nunca sobreposicao.

O `frequencia_hz * n_amostras` fecha com a mesma duracao total (em segundos)
pra todo canal do arquivo: essa e a invariante que teria substituido a soma
de bytes por bloco do `pi_pid` se este formato guardasse os canais
intercalados. Aqui nao guarda: cada bloco e continuo, entao a invariante
usada e a de offset consecutivo acima.

BUSCA SEM PONTEIRO DE CABECALHO: nao foi identificado, no cabecalho fixo do
arquivo, um ponteiro explicito pro inicio do dicionario (ao contrario do
`.ld`, que tem `ptr_canais` no offset 0x08). Em vez disso, ESTE LEITOR
BUSCA o dicionario dentro de uma janela limitada a partir do fim do
arquivo (`_JANELA_BUSCA_BYTES`), procurando a maior sequencia de registros
de 552 bytes em passo aritmetico cujo nome se repete em +88 (a assinatura
de validacao acima). A janela nunca materializa o arquivo inteiro: nos 25
arquivos decifrados, dicionario+tabela somam no maximo ~40 KB, bem dentro
da janela de alguns MB usada aqui.

ARQUIVOS QUE ESTE LEITOR REJEITA (medicao de 2026-09-14 em 71 arquivos
unicos do Drive, 27 abrem; lista por arquivo em `docs/pi-pds-medicao.md`):
- 10 arquivos de `Estudo/Cursos/Bootcamp_FullTime/` (layout de 304 bytes,
  sem nome duplicado em +88);
- 34 arquivos de `Porsche_Cup/` (Shakedown 2025, 26ET07 antigo, CLASS,
  FREE PRACTICE, RACE, REF 25ET6, REF38, REF 3.8, REF 991.2): ou nenhum
  candidato de 552 B nos ultimos 4 MB, ou candidatos de 8 a 52 canais sem
  nenhum registro de tabela valido logo em seguida. O dicionario real esta
  fora da janela ou tem outro layout; nao medido ainda. O leitor levanta
  `ErroDeLeitura` em vez de devolver inventario errado.
"""

from __future__ import annotations

import itertools
import struct
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from .base import Cabecalho, CanalBruto, ErroDeLeitura, LeitorDeInventario, Lote

_MAGIC: bytes = b"\x1a\x12\x40\xf7"
_OFF_MAGIC: int = 4
_TAMANHO_MINIMO: int = _OFF_MAGIC + len(_MAGIC)

# Layout do registro do dicionario (unico decifrado, ver docstring do
# modulo). Registros de 304 bytes (workbooks) NAO sao suportados.
_ESTRIDE_DICIONARIO: int = 552
_OFF_NOME: int = 0
_LEN_NOME_MAX: int = 40
_OFF_NOME_DUP: int = 88
_OFF_UNIDADE: int = 152
_OFF_IDX_DICIONARIO: int = 544

# Layout do registro da tabela de blocos de amostra.
_TAMANHO_REGISTRO_TABELA: int = 64
_OFF_TAB_IDX: int = 0
_OFF_TAB_INTERVALO: int = 16
_OFF_TAB_N_AMOSTRAS: int = 20
_OFF_TAB_BYTE_OFFSET: int = 48
_OFF_TAB_IDX_CHECK1: int = 56
_OFF_TAB_IDX_CHECK2: int = 60

#: Um tick vale 100 ns. Ver docstring do modulo: validado contra as 7
#: frequencias padrao (1, 5, 10, 20, 25, 50, 100 Hz) que aparecem no acervo.
_TICK_S: float = 1e-7
#: Tamanhos de amostra medidos no acervo (1, 2 e 4 bytes no 992.1, 8 nos
#: F3), usados so na invariante de offset (este leitor nunca le a amostra).
_TAMANHOS_DE_AMOSTRA: tuple[int, ...] = (1, 2, 4, 8)
#: Fracao minima de pares consecutivos (em ordem de offset) que fecham exato
#: com um dos tamanhos acima. Medido: 1,000 no F3 e 0,9995 no 992.1; um
#: candidato de ruido nao passa de poucos por cento (ver
#: `docs/pi-pds-medicao.md`).
_FRACAO_MINIMA_PARES_FECHADOS: float = 0.9

#: Janela de busca a partir do fim do arquivo. Generosa: o maior
#: dicionario+tabela medido no acervo (48 canais) soma ~29 KB.
_JANELA_BUSCA_BYTES: int = 4_000_000
#: Tamanho minimo de sequencia de registros pra considerar candidato a
#: dicionario real (contra ruido de amostra que por acaso repete em passo
#: 552 bytes, ver a secao de arquivos rejeitados na docstring do modulo).
_MIN_REGISTROS_CANDIDATO: int = 8
#: Teto minimo de canais com dado sobrevivendo ao cruzamento pra aceitar o
#: candidato. Sem isso, um candidato de ruido com so 1-2 registros de tabela
#: passa na invariante de offset por vacuidade (nao ha par consecutivo pra
#: checar): medido num arquivo do lote porsche-cup, ver secao de arquivos
#: rejeitados na docstring do modulo.
_MIN_CANAIS_COM_DADO: int = 8

#: Quantos candidatos (do maior pro menor) tentar antes de desistir. Ruido de
#: amostra reinterpretado como texto produz varios candidatos curtos que
#: nunca passam na invariante de offset (medido: ate ~90 candidatos num
#: arquivo so); o teto so existe pra nao rodar pra sempre num arquivo
#: patologico, nao pra limitar a busca no caso comum.
_MAX_CANDIDATOS_TENTADOS: int = 200


def _ler_string_u16(dados: bytes, offset: int, tamanho_max_chars: int) -> str | None:
    """Le uma string UTF-16LE terminada em par de bytes nulos.

    Devolve `None` (nunca lanca) quando o offset esta fora dos dados, o
    terminador nao aparece dentro do teto de caracteres, ou a decodificacao
    falha: usado tanto na busca (onde `None` so descarta o candidato) quanto
    na leitura confirmada (onde o chamador decide o que fazer com `None`).
    """
    fim_max = offset + tamanho_max_chars * 2
    if offset < 0 or offset + 2 > len(dados):
        return None
    fim = dados.find(b"\x00\x00", offset, fim_max)
    if fim < 0:
        return None
    if (fim - offset) % 2 == 1:
        fim += 1
    try:
        return dados[offset:fim].decode("utf-16le")
    except UnicodeDecodeError:
        return None


def _nome_valido(texto: str | None) -> bool:
    if texto is None or not (1 <= len(texto) <= _LEN_NOME_MAX):
        return False
    return all(32 <= ord(c) < 0x2500 for c in texto)


def _e_registro_dicionario(dados: bytes, offset: int) -> str | None:
    """Confirma um registro de dicionario pela assinatura nome==nome+88.

    Devolve o nome quando valido, `None` caso contrario. Este e o unico
    filtro contra ruido de amostra reinterpretado como texto: um `float64`
    aleatorio raramente produz UM nome plausivel, e produzir DOIS iguais a
    88 bytes de distancia por acaso e raro o bastante pra servir de sinal
    (mas nao suficiente sozinho: ver invariante de offset na tabela).
    """
    nome = _ler_string_u16(dados, offset + _OFF_NOME, _LEN_NOME_MAX)
    if not _nome_valido(nome):
        return None
    nome_dup = _ler_string_u16(dados, offset + _OFF_NOME_DUP, _LEN_NOME_MAX)
    if nome_dup != nome:
        return None
    return nome


def _candidatos_dicionario(dados: bytes) -> list[tuple[int, int]]:
    """Acha sequencias de registros validos em passo aritmetico de 552 B.

    Devolve `(offset_inicio, n_registros)` pra cada sequencia de pelo menos
    `_MIN_REGISTROS_CANDIDATO` registros, ordenada da maior pra menor.
    """
    validos: set[int] = set()
    limite = len(dados) - _ESTRIDE_DICIONARIO - _OFF_NOME_DUP - 4
    offset = 0
    while offset < limite:
        if _e_registro_dicionario(dados, offset) is not None:
            validos.add(offset)
        offset += 2

    candidatos: list[tuple[int, int]] = []
    visitados: set[int] = set()
    for v in validos:
        inicio = v
        while (inicio - _ESTRIDE_DICIONARIO) in validos:
            inicio -= _ESTRIDE_DICIONARIO
        if inicio in visitados:
            continue
        visitados.add(inicio)
        n = 0
        p = inicio
        while p in validos:
            n += 1
            p += _ESTRIDE_DICIONARIO
        if n >= _MIN_REGISTROS_CANDIDATO:
            candidatos.append((inicio, n))

    # Maior sequencia primeiro; em empate, o menor offset: um nome UTF-16
    # sem o primeiro caractere ainda repete em +88, entao cada dicionario
    # real gera copias deslocadas em +2 e +4 B, e a verdadeira e a primeira.
    candidatos.sort(key=lambda c: (-c[1], c[0]))
    return candidatos


@dataclass(frozen=True)
class _BlocoTabela:
    idx: int
    intervalo_ticks: int
    n_amostras: int
    byte_offset: int


def _ler_tabela(
    dados: bytes, offset_inicio: int, n_dicionario: int, offset_dicionario_abs: int
) -> list[_BlocoTabela]:
    """Le a tabela de blocos de amostra, um registro de 64 B por vez.

    `offset_dicionario_abs` e absoluto no arquivo (o offset de bloco da
    tabela tambem e): todo bloco de amostra termina antes do dicionario.

    Para no primeiro registro invalido (fim natural da tabela). Um canal pode
    aparecer em varios registros (varios blocos), ver docstring do modulo.
    """
    blocos: list[_BlocoTabela] = []
    p = offset_inicio
    while p + _TAMANHO_REGISTRO_TABELA <= len(dados):
        idx = struct.unpack_from("<i", dados, p + _OFF_TAB_IDX)[0]
        intervalo = struct.unpack_from("<i", dados, p + _OFF_TAB_INTERVALO)[0]
        n_amostras = struct.unpack_from("<i", dados, p + _OFF_TAB_N_AMOSTRAS)[0]
        byte_offset = struct.unpack_from("<i", dados, p + _OFF_TAB_BYTE_OFFSET)[0]

        if intervalo <= 0 or n_amostras <= 0:
            break
        if not (0 <= idx < n_dicionario):
            break
        if byte_offset <= 0 or byte_offset + n_amostras > offset_dicionario_abs:
            break

        blocos.append(_BlocoTabela(idx, intervalo, n_amostras, byte_offset))
        p += _TAMANHO_REGISTRO_TABELA

    return blocos


def _checar_invariante_offset(
    blocos: list[_BlocoTabela], caminho: Path
) -> tuple[int, int]:
    """Blocos em ordem de offset: a distancia ate o proximo tem que ser o
    numero de amostras vezes 1, 2, 4 ou 8 bytes.

    Devolve `(pares_fechados, buracos)`. Sobreposicao (distancia menor que
    uma amostra por ponto) derruba o arquivo: a tabela decodificada nao e
    confiavel. Buraco (distancia maior que 8 por amostra sem fechar exato)
    e tolerado ate o teto de `_FRACAO_MINIMA_PARES_FECHADOS`, ver docstring
    do modulo.
    """
    ordenados = sorted(blocos, key=lambda b: b.byte_offset)
    fechados = 0
    buracos = 0
    for anterior, atual in itertools.pairwise(ordenados):
        distancia = atual.byte_offset - anterior.byte_offset
        if distancia < anterior.n_amostras:
            raise ErroDeLeitura(
                f"{caminho}: blocos de amostra sobrepostos na tabela: canal "
                f"{anterior.idx} em offset {anterior.byte_offset} com "
                f"{anterior.n_amostras} amostras e canal {atual.idx} em offset "
                f"{atual.byte_offset}. A tabela decodificada nao e confiavel."
            )
        if any(distancia == anterior.n_amostras * t for t in _TAMANHOS_DE_AMOSTRA):
            fechados += 1
        else:
            buracos += 1
    pares = fechados + buracos
    if pares and fechados / pares < _FRACAO_MINIMA_PARES_FECHADOS:
        raise ErroDeLeitura(
            f"{caminho}: so {fechados} de {pares} pares consecutivos de blocos "
            f"fecham com 1, 2, 4 ou 8 bytes por amostra (minimo "
            f"{_FRACAO_MINIMA_PARES_FECHADOS:.0%}). A tabela decodificada nao e "
            "confiavel."
        )
    return fechados, buracos


class LeitorPiPds(LeitorDeInventario):
    """Container Pi Toolbox `.pds`, formato `pi_pds`.

    Le o dicionario de canais e a tabela de blocos de amostra perto do fim
    do arquivo (inspecionar) e le a amostra em streaming de 64 KB (ler).
    """

    formato_id = "pi_pds"
    versao = "1"
    suporta_amostra = True

    def ler(self, caminho: Path) -> Iterator[Lote]:
        from telemetria.leitores.cosworth_pi import CosworthPdsReader

        return CosworthPdsReader().ler(caminho)

    def inspecionar(self, caminho: Path) -> Cabecalho:
        tamanho_arquivo = caminho.stat().st_size
        if tamanho_arquivo < _TAMANHO_MINIMO:
            raise ErroDeLeitura(
                f"{caminho}: arquivo com {tamanho_arquivo} B, menor que o "
                f"magic em offset {_OFF_MAGIC} ({_TAMANHO_MINIMO} B minimos)"
            )

        with caminho.open("rb") as fh:
            fh.seek(_OFF_MAGIC)
            magic = fh.read(len(_MAGIC))
            if magic != _MAGIC:
                raise ErroDeLeitura(
                    f"{caminho}: magic {magic!r} != {_MAGIC!r} esperado em "
                    f"offset {_OFF_MAGIC}, nao e pi_pds"
                )

            janela = min(_JANELA_BUSCA_BYTES, tamanho_arquivo)
            base = tamanho_arquivo - janela
            fh.seek(base)
            dados = fh.read(janela)

        candidatos = _candidatos_dicionario(dados)
        if not candidatos:
            raise ErroDeLeitura(
                f"{caminho}: nenhum dicionario de canais encontrado nos "
                f"ultimos {janela} B do arquivo (offset absoluto >= {base}). "
                "Layout de registro de 552 B (ver docstring do modulo) nao "
                "bateu em nenhuma sequencia de pelo menos "
                f"{_MIN_REGISTROS_CANDIDATO} canais; se o arquivo usa o "
                "layout de 304 B (lote workbooks) ou concatena varias "
                "capturas (lote porsche-cup, arquivos grandes), este leitor "
                "nao suporta ainda."
            )

        erro_maior_candidato: ErroDeLeitura | None = None
        for offset_dicionario, n_dicionario in candidatos[:_MAX_CANDIDATOS_TENTADOS]:
            try:
                return self._montar_cabecalho(
                    dados, base, offset_dicionario, n_dicionario, caminho
                )
            except ErroDeLeitura as erro:
                if erro_maior_candidato is None:
                    erro_maior_candidato = erro
                continue

        assert erro_maior_candidato is not None
        raise ErroDeLeitura(
            f"{caminho}: {len(candidatos)} candidato(s) a dicionario "
            f"encontrado(s) nos ultimos {janela} B, nenhum passou na "
            f"invariante de offset da tabela. Erro do maior candidato: "
            f"{erro_maior_candidato}"
        )

    def _montar_cabecalho(
        self,
        dados: bytes,
        base: int,
        offset_dicionario: int,
        n_dicionario: int,
        caminho: Path,
    ) -> Cabecalho:
        nomes_por_idx: dict[int, tuple[str, str | None]] = {}
        idx_ambiguos: set[int] = set()
        for i in range(n_dicionario):
            registro = offset_dicionario + i * _ESTRIDE_DICIONARIO
            nome = _ler_string_u16(dados, registro + _OFF_NOME, _LEN_NOME_MAX)
            if not nome:
                raise ErroDeLeitura(
                    f"{caminho}: registro de dicionario em offset absoluto "
                    f"{registro + base} sem nome legivel"
                )
            unidade = _ler_string_u16(dados, registro + _OFF_UNIDADE, 20)
            idx = struct.unpack_from("<i", dados, registro + _OFF_IDX_DICIONARIO)[0]
            if idx in nomes_por_idx and nomes_por_idx[idx][0] != nome:
                # Indice repetido com nome diferente: pelo menos um dos dois
                # canais nao tem dado nesta captura e o campo de indice do
                # dicionario ficou com um valor de preenchimento (medido:
                # sempre 0). Nenhum dos dois entra no inventario: escolher
                # um seria adivinhar qual tem o dado de verdade.
                idx_ambiguos.add(idx)
            else:
                nomes_por_idx[idx] = (nome, unidade or None)

        tabela_offset = offset_dicionario + n_dicionario * _ESTRIDE_DICIONARIO
        blocos = _ler_tabela(
            dados, tabela_offset, n_dicionario, offset_dicionario + base
        )
        if not blocos:
            raise ErroDeLeitura(
                f"{caminho}: dicionario com {n_dicionario} canais em offset "
                f"absoluto {offset_dicionario + base}, mas nenhum registro de "
                f"tabela valido logo em seguida (offset absoluto "
                f"{tabela_offset + base})"
            )
        fechados, buracos = _checar_invariante_offset(blocos, caminho)

        # Um canal pode ter varios blocos: soma as amostras, exige o mesmo
        # intervalo em todos (medido: vale nos 2485 canais do 992.1).
        por_idx: dict[int, list[_BlocoTabela]] = {}
        for bloco in blocos:
            por_idx.setdefault(bloco.idx, []).append(bloco)

        canais = []
        for idx in sorted(por_idx):
            if idx in idx_ambiguos or idx not in nomes_por_idx:
                continue
            nome, unidade = nomes_por_idx[idx]
            intervalos = {b.intervalo_ticks for b in por_idx[idx]}
            if len(intervalos) != 1:
                raise ErroDeLeitura(
                    f"{caminho}: canal {nome!r} (indice {idx}) tem blocos com "
                    f"intervalos diferentes {sorted(intervalos)} ticks; este "
                    "leitor nao decide a frequencia dele."
                )
            frequencia_hz = 1.0 / (intervalos.pop() * _TICK_S)
            canais.append(
                CanalBruto(
                    nome_bruto=nome,
                    frequencia_hz=frequencia_hz,
                    n_amostras=sum(b.n_amostras for b in por_idx[idx]),
                    unidade_declarada=unidade,
                )
            )

        if len(canais) < _MIN_CANAIS_COM_DADO:
            raise ErroDeLeitura(
                f"{caminho}: so {len(canais)} canal(is) sobrou(aram) depois "
                f"de cruzar indice (minimo {_MIN_CANAIS_COM_DADO}): "
                f"dicionario tinha {n_dicionario} canais, tabela tinha "
                f"{len(blocos)} registros. Provavel candidato de ruido "
                "(ver invariante de offset vazia com poucos registros na "
                "docstring do modulo), nao um dicionario real."
            )

        canal_mais_longo = max(canais, key=lambda c: c.n_amostras)
        duracao_s = canal_mais_longo.n_amostras / canal_mais_longo.frequencia_hz

        bruto: dict[str, str] = {
            "offset_dicionario": str(offset_dicionario + base),
            "n_canais_dicionario": str(n_dicionario),
            "n_canais_com_dado": str(len(canais)),
            "n_canais_sem_dado": str(n_dicionario - len(canais)),
            "offset_tabela": str(tabela_offset + base),
            "n_registros_tabela": str(len(blocos)),
            "n_pares_fechados": str(fechados),
            "n_buracos": str(buracos),
        }

        return Cabecalho(
            formato_id=self.formato_id,
            leitor_versao=self.versao,
            canais=tuple(canais),
            capturado_em=None,
            duracao_s=duracao_s,
            venue_declarado=None,
            bruto=bruto,
        )
