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
   registros de 64 bytes, um por canal QUE TEM DADO (um canal do dicionario
   pode nao ter registro aqui: medido em varios arquivos do acervo, o
   dicionario declara N canais e a tabela cobre N-1, o canal ausente fica
   sem amostra gravada nesta captura). Campos medidos (todos `<i` de 4
   bytes, offsets relativos ao inicio do registro de 64 bytes):
   - offset 0: indice do canal (0-based, mesmo espaco do offset 544 do
     dicionario).
   - offset 16: intervalo entre amostras, em unidades de 1e-7 s (100 ns).
     `frequencia_hz = 1e7 / intervalo`. Validado contra os 7 valores que
     aparecem no acervo (100, 50, 25, 20, 10, 5 e 1 Hz), todos frequencias
     de log padrao de telemetria automotiva.
   - offset 20: numero de amostras do canal nesta captura.
   - offset 48: offset (em bytes, a partir do inicio do arquivo) de onde
     comecam as amostras `float64` deste canal. NAO lido por este leitor
     (inventario, nao amostra), mas serve de invariante: a diferenca de
     offset entre dois registros consecutivos da tabela tem que fechar
     exato com `n_amostras_do_anterior * 8` (8 bytes por amostra
     `float64`). Fechou em 100% dos registros consecutivos nos 25 arquivos
     do acervo que este leitor conseguiu decifrar.
   - offsets 56 e 60: o indice do canal (offset 0) mais 1, repetido duas
     vezes. Serve de checksum barato do registro: se nao bater, o registro
     nao e mais tabela (fim da tabela).

O `frequencia_hz * n_amostras` fecha com a mesma duracao total (em segundos)
pra todo canal do arquivo: essa e a invariante que teria substituido a soma
de bytes por bloco do `pi_pid` se este formato guardasse os canais
intercalados. Aqui nao guarda: cada canal tem seu proprio bloco continuo de
`float64`, entao a invariante usada e a de offset consecutivo acima.

BUSCA SEM PONTEIRO DE CABECALHO: nao foi identificado, no cabecalho fixo do
arquivo, um ponteiro explicito pro inicio do dicionario (ao contrario do
`.ld`, que tem `ptr_canais` no offset 0x08). Em vez disso, ESTE LEITOR
BUSCA o dicionario dentro de uma janela limitada a partir do fim do
arquivo (`_JANELA_BUSCA_BYTES`), procurando a maior sequencia de registros
de 552 bytes em passo aritmetico cujo nome se repete em +88 (a assinatura
de validacao acima). A janela nunca materializa o arquivo inteiro: nos 25
arquivos decifrados, dicionario+tabela somam no maximo ~40 KB, bem dentro
da janela de alguns MB usada aqui.

ARQUIVOS QUE ESTE LEITOR REJEITA (divida declarada, nao lida por falta de
medicao, ver `docs/pi-pds-medicao.md`):
- os 10 arquivos de `workbooks/pi-toolbox-bootcamp/` (layout de 304 bytes,
  sem indice de canal identificavel no registro do dicionario);
- ao menos 9 arquivos de `telemetria/porsche-cup/` (os de "Shakedown", o
  `CLASS.pds` e o `REF 991.2.pds`): sao grandes demais (25-98 MB) e
  parecem conter VARIOS dicionarios concatenados (varias capturas num
  arquivo so, um caso de arquitetura que este leitor nao decide sozinho:
  ver a secao correspondente no relatorio de entrega). A busca deste
  leitor encontra ruido de amostra que por acaso repete em passo 552 bytes
  dentro da janela e a invariante de offset rejeita o resultado, entao o
  arquivo levanta `ErroDeLeitura` em vez de devolver inventario errado.
"""

from __future__ import annotations

import itertools
import struct
from dataclasses import dataclass
from pathlib import Path

from .base import Cabecalho, CanalBruto, ErroDeLeitura, LeitorDeInventario

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
#: `float64`: 8 bytes por amostra, usado so na invariante de offset (este
#: leitor nunca le a amostra em si).
_BYTES_POR_AMOSTRA: int = 8

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

    candidatos.sort(key=lambda c: c[1], reverse=True)
    return candidatos


@dataclass(frozen=True)
class _EntradaTabela:
    intervalo_ticks: int
    n_amostras: int
    byte_offset: int


def _ler_tabela(dados: bytes, offset_inicio: int) -> dict[int, _EntradaTabela]:
    """Le a tabela de blocos de amostra, um registro de 64 B por vez.

    Para no primeiro registro invalido (fim natural da tabela: nem todo
    arquivo tem registro de tabela pra todos os canais do dicionario, ver
    docstring do modulo).
    """
    entradas: dict[int, _EntradaTabela] = {}
    p = offset_inicio
    while p + _TAMANHO_REGISTRO_TABELA <= len(dados):
        idx = struct.unpack_from("<i", dados, p + _OFF_TAB_IDX)[0]
        intervalo = struct.unpack_from("<i", dados, p + _OFF_TAB_INTERVALO)[0]
        n_amostras = struct.unpack_from("<i", dados, p + _OFF_TAB_N_AMOSTRAS)[0]
        byte_offset = struct.unpack_from("<i", dados, p + _OFF_TAB_BYTE_OFFSET)[0]
        check1 = struct.unpack_from("<i", dados, p + _OFF_TAB_IDX_CHECK1)[0]
        check2 = struct.unpack_from("<i", dados, p + _OFF_TAB_IDX_CHECK2)[0]

        if intervalo <= 0 or n_amostras <= 0:
            break
        if not (check1 == check2 == idx + 1):
            break

        entradas[idx] = _EntradaTabela(intervalo, n_amostras, byte_offset)
        p += _TAMANHO_REGISTRO_TABELA

    return entradas


def _checar_invariante_offset(
    entradas: dict[int, _EntradaTabela], caminho: Path
) -> None:
    """A tabela e lida em ordem fisica (= ordem de indice, ver docstring).

    O offset de bytes de um registro tem que ser exatamente o offset do
    anterior mais `n_amostras * 8` (float64): e o unico jeito barato de
    confirmar que decodificamos os campos certos, sem ler a amostra em si.
    Um so registro que nao feche derruba o arquivo inteiro: e a mesma
    postura do `pi_pid` pra soma de bytes por bloco.
    """
    indices = sorted(entradas)
    for anterior, atual in itertools.pairwise(indices):
        e_anterior = entradas[anterior]
        e_atual = entradas[atual]
        esperado = e_anterior.byte_offset + e_anterior.n_amostras * _BYTES_POR_AMOSTRA
        if e_atual.byte_offset != esperado:
            raise ErroDeLeitura(
                f"{caminho}: invariante de offset quebrada entre os canais de "
                f"indice {anterior} e {atual} da tabela: esperava offset "
                f"{esperado}, achou {e_atual.byte_offset}. A tabela decodificada "
                "nao e confiavel."
            )


class LeitorPiPds(LeitorDeInventario):
    """Inventario de canal do container Pi Toolbox `.pds`.

    So le o dicionario de canais e a tabela de blocos de amostra, ambos
    perto do fim do arquivo (busca limitada a `_JANELA_BUSCA_BYTES`): nunca
    o corpo de amostra `float64`, que fica entre o cabecalho fixo e o
    dicionario.
    """

    formato_id = "pi_pds"
    versao = "1"

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

        erro_ultimo_candidato: ErroDeLeitura | None = None
        for offset_dicionario, n_dicionario in candidatos[:_MAX_CANDIDATOS_TENTADOS]:
            try:
                return self._montar_cabecalho(
                    dados, base, offset_dicionario, n_dicionario, caminho
                )
            except ErroDeLeitura as erro:
                erro_ultimo_candidato = erro
                continue

        assert erro_ultimo_candidato is not None
        raise ErroDeLeitura(
            f"{caminho}: {len(candidatos)} candidato(s) a dicionario "
            f"encontrado(s) nos ultimos {janela} B, nenhum passou na "
            f"invariante de offset da tabela. Ultimo erro: {erro_ultimo_candidato}"
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
        entradas = _ler_tabela(dados, tabela_offset)
        if not entradas:
            raise ErroDeLeitura(
                f"{caminho}: dicionario com {n_dicionario} canais em offset "
                f"absoluto {offset_dicionario + base}, mas nenhum registro de "
                f"tabela valido logo em seguida (offset absoluto "
                f"{tabela_offset + base})"
            )
        _checar_invariante_offset(entradas, caminho)

        canais = []
        for idx in sorted(entradas):
            if idx in idx_ambiguos or idx not in nomes_por_idx:
                continue
            nome, unidade = nomes_por_idx[idx]
            entrada = entradas[idx]
            frequencia_hz = _TICK_S and 1.0 / (entrada.intervalo_ticks * _TICK_S)
            canais.append(
                CanalBruto(
                    nome_bruto=nome,
                    frequencia_hz=frequencia_hz,
                    n_amostras=entrada.n_amostras,
                    unidade_declarada=unidade,
                )
            )

        if len(canais) < _MIN_CANAIS_COM_DADO:
            raise ErroDeLeitura(
                f"{caminho}: so {len(canais)} canal(is) sobrou(aram) depois "
                f"de cruzar indice (minimo {_MIN_CANAIS_COM_DADO}): "
                f"dicionario tinha {n_dicionario} canais, tabela tinha "
                f"{len(entradas)} registros. Provavel candidato de ruido "
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
            "n_registros_tabela": str(len(entradas)),
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
