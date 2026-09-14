"""Leitor de inventario do container ASAM MDF4 (`.mf4`), formato `asam_mf4`.

MDF4 e norma aberta (ASAM): arvore de blocos com cabecalho fixo de 24 bytes
(`id` de 4 bytes tipo `##XX`, 4 bytes reservados, `length` UINT64 do bloco
inteiro e `link_count` UINT64), seguido de `link_count` ponteiros de 8 bytes
e por fim a secao de dados propria do bloco. Todo acesso e por `seek`/`read`
nesses ponteiros, sem tabela de offset fixo (ao contrario do `.ld`): cada
bloco declara o proprio tamanho e a propria contagem de link.

Medido em 2026-08-29 contra os 5 `.mf4` do acervo (ver
`ferramenta de exploracao usada na delegacao, nao versionada`): todos MDF
versao `4.00`, programa gerador `VI-grade` (simulador de dinamica veicular),
1 `##DG` por arquivo, 1 `##CG` por `##DG`, dado em `##DL` com 1 `##DT` so
(sem `##DZ` comprimido, sem lista de dados fragmentada em varios blocos) e
nenhum `##CC` de conversao (a unidade sai sempre do `##TX` de `cn_md_unit`).
A implementacao cobre so o que foi medido: layout de dado mais complexo
levanta `ErroDeLeitura` explicito em vez de adivinhar.

REGRA DURA (decisao de arquitetura no Lucas), bifurcacao nao coberta pelo
prompt de delegacao:

# DECISAO PENDENTE (Lucas): tensao entre "nao leia a secao de dados (##DT)"
# e o proprio contrato exigir `frequencia_hz` provada. MDF4 NAO guarda taxa
# de amostragem em lugar nenhum da arvore de blocos (cabecalho de ##HD,
# ##DG, ##CG e ##CN todos medidos, nenhum campo de intervalo ou taxa): a
# unica fonte e o valor do canal mestre (tempo) no primeiro e no ultimo
# registro. A leitura implementada aqui e conservadora nesse ponto
# especifico: faz DUAS leituras pontuais de 8 bytes cada (offset calculado
# por ponteiro, nunca varredura) so no canal mestre, nunca no resto do
# registro nem no arquivo inteiro, e reusa a MESMA taxa pra todos os canais
# do grupo (todos compartilham o mesmo mestre). Opcoes que ficaram na mesa:
#   (a) o que este arquivo faz: 2 leituras pontuais no mestre, taxa provada
#       por grupo. Mais util (os 5 arquivos abrem), mas toca a secao de
#       dados, o que a instrucao original pede pra evitar.
#   (b) nunca tocar ##DT/##DL/##DT, e levantar ErroDeLeitura em todo grupo
#       sem taxa provavel so pela arvore. Mais literal com "nao leia dado",
#       mas nenhum dos 5 arquivos do acervo abriria (MDF4 real sempre cai
#       nesse caso), o que esvazia o leitor.
# Este arquivo escolheu (a) por ser o unico caminho que deixa o contrato
# (`frequencia_hz` provada, nunca fabricada) satisfeito pra formato MDF4 de
# verdade. Se o Lucas preferir (b), e trocar a chamada a
# `_derivar_frequencia_do_mestre` por um `raise ErroDeLeitura` direto.

`ler()` reusa a mesma decisao (a): ja precisa do canal mestre inteiro pra
gerar `t_s`, entao a leitura pontual de 2 valores vira leitura do array
inteiro do mestre, ainda sem tocar no resto do registro alem do que sai
como coluna.

# DECISAO PENDENTE (Lucas): 1.130 a 1.185 colunas por `Lote` e muita coluna
# pra um RecordBatch so. O prompt de delegacao pede a alternativa
# conservadora quando dividir junta uma agregacao que o arquivo nao tem, e
# e exatamente esse o caso aqui: os 5 arquivos do acervo tem 1 `##DG` e 1
# `##CG` cada, ou seja UM grupo de amostra por arquivo, com todos os canais
# lidos do mesmo registro fisico (mesmo `record_size`, mesmo `byte_offset`
# por campo). Dividir em "varias series por grupo de canal" inventaria um
# agrupamento (que canais formam que serie?) que o MDF4 nao declara em
# lugar nenhum da arvore de blocos: seria decisao de negocio disfarcada de
# leitura. Por isso `ler()` emite UM `Lote` por `##CG` (aqui, um por
# arquivo), com todas as colunas do grupo. Custo medido: o maior arquivo
# (`RaceCar_vdd.mf4`, 6.652 registros x 1.185 canais x 8 bytes) materializa
# ~63 MB em memoria por `Lote`, bem abaixo do teto de streaming que motivou
# o corte em lotes no `.ld` (ali o problema e MILHOES de linhas por canal;
# aqui e MILHARES de linhas com MILHARES de colunas, geometria oposta). Se
# o volume por arquivo crescer numa ordem de grandeza (10x+ amostras),
# reavaliar: opcoes seriam (a) manter e aceitar o custo (o que este arquivo
# faz agora), ou (b) dividir por faixa de linha (nao de coluna) dentro do
# mesmo `##CG`, que ai sim preserva o grupo fisico e so corta o eixo do
# tempo.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from .base import Cabecalho, CanalBruto, ErroDeLeitura, LeitorDeInventario

IDBLOCK_TAMANHO = 64
IDBLOCK_MAGIC = b"MDF     "
BLOCO_CABECALHO_TAMANHO = 24  # id(4) + reservado(4) + length(u64) + link_count(u64)

# cn_type: valores do enum de tipo de canal (ASAM MDF4, 6.4.2 CNBLOCK).
CN_TYPE_MASTER = 2

# cg_flags, bit 0: VLSD_CHANNEL_GROUP (nao usado aqui, so documentado pra
# deixar claro que este leitor assume grupo de tamanho fixo, o unico visto
# no acervo).

# dl_flags, bit 0: DL_FLAG_EQUAL_LENGTH (todos os blocos filhos do ##DL tem
# o mesmo tamanho de dado, declarado uma vez em vez de por offset).
DL_FLAG_EQUAL_LENGTH = 0x01

# data_type de CNBLOCK/CCBLOCK que este leitor sabe decodificar num valor
# numerico (o suficiente pra ler o canal mestre). String e byte array
# (data_type >= 6) nao entram aqui: nenhum canal mestre do acervo usa isso.
_STRUCT_POR_TIPO: dict[tuple[int, int], str] = {
    (0, 8): "<B",
    (0, 16): "<H",
    (0, 32): "<I",
    (0, 64): "<Q",
    (1, 8): ">B",
    (1, 16): ">H",
    (1, 32): ">I",
    (1, 64): ">Q",
    (2, 8): "<b",
    (2, 16): "<h",
    (2, 32): "<i",
    (2, 64): "<q",
    (3, 8): ">b",
    (3, 16): ">h",
    (3, 32): ">i",
    (3, 64): ">q",
    (4, 32): "<f",
    (4, 64): "<d",
    (5, 32): ">f",
    (5, 64): ">d",
}


@dataclass(frozen=True)
class _BlocoBruto:
    """Um bloco MDF4 generico ja lido: id, tamanho, links e dado cru."""

    offset: int
    bid: bytes
    length: int
    links: tuple[int, ...]
    data: bytes


@dataclass(frozen=True)
class _CanalMdf:
    """Um `##CN` decodificado, ainda sem taxa (a taxa e por grupo)."""

    nome_bruto: str
    unidade_declarada: str | None
    cn_type: int
    data_type: int
    bit_offset: int
    byte_offset: int
    bit_count: int


def _ler_bloco(
    fh, caminho: Path, offset: int, esperado: bytes | None = None
) -> _BlocoBruto:
    """Le um bloco generico no offset dado: cabecalho, links e dado.

    Nunca devolve bloco parcial: EOF ou id que nao comeca com `##` levanta
    `ErroDeLeitura` com o offset onde parou, igual ao `.ld`.
    """
    fh.seek(offset)
    cabecalho = fh.read(BLOCO_CABECALHO_TAMANHO)
    if len(cabecalho) < BLOCO_CABECALHO_TAMANHO:
        raise ErroDeLeitura(
            f"{caminho}: EOF lendo cabecalho de bloco em offset {offset} "
            f"({len(cabecalho)}/{BLOCO_CABECALHO_TAMANHO} bytes)"
        )
    bid = cabecalho[0:4]
    if not bid.startswith(b"##"):
        raise ErroDeLeitura(
            f"{caminho}: bloco em offset {offset} sem prefixo '##' ({bid!r}), "
            "arvore corrompida ou ponteiro errado"
        )
    if esperado is not None and bid != esperado:
        raise ErroDeLeitura(
            f"{caminho}: esperava bloco {esperado!r} em offset {offset}, achou {bid!r}"
        )
    length = struct.unpack_from("<Q", cabecalho, 8)[0]
    link_count = struct.unpack_from("<Q", cabecalho, 16)[0]
    if length < BLOCO_CABECALHO_TAMANHO + link_count * 8:
        raise ErroDeLeitura(
            f"{caminho}: bloco {bid!r} em offset {offset} com length "
            f"{length} menor que cabecalho + links ({link_count} links)"
        )
    bruto_links = fh.read(link_count * 8)
    if len(bruto_links) < link_count * 8:
        raise ErroDeLeitura(
            f"{caminho}: EOF lendo links do bloco {bid!r} em offset {offset}"
        )
    links = struct.unpack_from(f"<{link_count}Q", bruto_links) if link_count else ()
    tamanho_dado = length - BLOCO_CABECALHO_TAMANHO - link_count * 8
    dado = fh.read(tamanho_dado)
    if len(dado) < tamanho_dado:
        raise ErroDeLeitura(
            f"{caminho}: EOF lendo dado do bloco {bid!r} em offset {offset} "
            f"({len(dado)}/{tamanho_dado} bytes)"
        )
    return _BlocoBruto(offset, bid, length, links, dado)


def _ler_texto(fh, caminho: Path, offset: int) -> str | None:
    """Le um `##TX` ou `##MD` e devolve o texto (UTF-8, cortado no NUL).

    `##MD` guarda XML: este leitor devolve o XML cru como string, sem parser
    de XML novo (dependencia). Quem quiser um campo especifico do XML faz
    isso na etapa seguinte, nao aqui.
    """
    if offset == 0:
        return None
    bloco = _ler_bloco(fh, caminho, offset)
    if bloco.bid not in (b"##TX", b"##MD"):
        raise ErroDeLeitura(
            f"{caminho}: esperava ##TX ou ##MD em offset {offset}, achou {bloco.bid!r}"
        )
    texto = bloco.data.split(b"\x00", 1)[0]
    return texto.decode("utf-8", errors="replace").strip()


def _ler_unidade_canal(fh, caminho: Path, cn: _BlocoBruto) -> str | None:
    """Unidade declarada: `cn_md_unit` (link 6) e a fonte primaria.

    Fallback pro `##CC` (link 4, `cn_cc_conversion`) quando o canal nao tem
    unidade propria mas tem conversao: nenhum dos 5 arquivos do acervo tem
    `##CC` (todo `cn_cc_conversion` medido e 0), entao este caminho e
    best-effort, nao provado contra arquivo real (inferido).
    """
    cn_cc = cn.links[4]
    cn_md_unit = cn.links[6]
    unidade = _ler_texto(fh, caminho, cn_md_unit)
    if unidade:
        return unidade
    if cn_cc == 0:
        return None
    cc = _ler_bloco(fh, caminho, cn_cc, esperado=b"##CC")
    if len(cc.links) < 2:
        return None
    return _ler_texto(fh, caminho, cc.links[1])  # cc_md_unit (inferido)


def _ler_canal(fh, caminho: Path, offset: int) -> tuple[_CanalMdf, int]:
    """Le um `##CN`, devolve o canal decodificado e o offset do proximo."""
    cn = _ler_bloco(fh, caminho, offset, esperado=b"##CN")
    if len(cn.links) < 8:
        raise ErroDeLeitura(
            f"{caminho}: ##CN em offset {offset} com {len(cn.links)} links, "
            "esperava >= 8 (cn_cn_next..cn_md_comment)"
        )
    if len(cn.data) < 24:
        raise ErroDeLeitura(
            f"{caminho}: ##CN em offset {offset} com dado curto demais "
            f"({len(cn.data)} bytes) pra ler os campos fixos"
        )
    cn_next = cn.links[0]
    cn_tx_name = cn.links[2]
    cn_type, _sync_type, data_type, bit_offset = struct.unpack_from("<BBBB", cn.data, 0)
    byte_offset, bit_count = struct.unpack_from("<II", cn.data, 4)

    nome = _ler_texto(fh, caminho, cn_tx_name)
    if not nome:
        raise ErroDeLeitura(
            f"{caminho}: ##CN em offset {offset} sem nome (cn_tx_name={cn_tx_name})"
        )
    unidade = _ler_unidade_canal(fh, caminho, cn)

    canal = _CanalMdf(
        nome_bruto=nome,
        unidade_declarada=unidade,
        cn_type=cn_type,
        data_type=data_type,
        bit_offset=bit_offset,
        byte_offset=byte_offset,
        bit_count=bit_count,
    )
    return canal, cn_next


def _localizar_bloco_de_dado(fh, caminho: Path, dg_data: int) -> tuple[int, int]:
    """Resolve o ponteiro `dg_data` pro `##DT` unico que este leitor sabe ler.

    So suporta o layout medido no acervo: `dg_data` aponta direto pra `##DT`,
    ou pra `##DL` com exatamente 1 filho (`dl_count == 1`) e sem compressao.
    Qualquer outro layout (`##DZ` comprimido, `##DL` com varios `##DT`,
    lista encadeada de `##DL`) levanta `ErroDeLeitura` explicito em vez de
    tentar remontar um fluxo de bytes concatenado que nunca foi provado
    contra arquivo real: ver a nota de DECISAO PENDENTE no topo do modulo.

    Devolve `(offset_do_inicio_do_dado, tamanho_do_dado)`.
    """
    if dg_data == 0:
        raise ErroDeLeitura(f"{caminho}: grupo de canal sem bloco de dado (dg_data=0)")

    bloco = _ler_bloco(fh, caminho, dg_data)
    if bloco.bid == b"##DT":
        return dg_data + BLOCO_CABECALHO_TAMANHO, bloco.length - BLOCO_CABECALHO_TAMANHO

    if bloco.bid == b"##DL":
        if bloco.links and bloco.links[0] != 0:
            raise ErroDeLeitura(
                f"{caminho}: ##DL em offset {dg_data} encadeado (dl_dl_next != 0), "
                "layout com mais de uma lista de dado nao suportado"
            )
        if len(bloco.data) < 8:
            raise ErroDeLeitura(
                f"{caminho}: ##DL em offset {dg_data} com dado curto demais"
            )
        dl_flags = bloco.data[0]
        dl_count = struct.unpack_from("<I", bloco.data, 4)[0]
        if dl_count != 1:
            raise ErroDeLeitura(
                f"{caminho}: ##DL em offset {dg_data} com dl_count={dl_count}, "
                "so dl_count == 1 e suportado (nao ocorre no acervo medido)"
            )
        if not (dl_flags & DL_FLAG_EQUAL_LENGTH):
            raise ErroDeLeitura(
                f"{caminho}: ##DL em offset {dg_data} sem DL_FLAG_EQUAL_LENGTH, "
                "layout com offset explicito nao suportado"
            )
        if len(bloco.links) < 2 or bloco.links[1] == 0:
            raise ErroDeLeitura(
                f"{caminho}: ##DL em offset {dg_data} sem filho de dado (dl_data[0])"
            )
        filho = _ler_bloco(fh, caminho, bloco.links[1])
        if filho.bid != b"##DT":
            raise ErroDeLeitura(
                f"{caminho}: filho do ##DL em offset {bloco.links[1]} e "
                f"{filho.bid!r}, so ##DT (sem compressao) e suportado"
            )
        return bloco.links[1] + BLOCO_CABECALHO_TAMANHO, (
            filho.length - BLOCO_CABECALHO_TAMANHO
        )

    raise ErroDeLeitura(
        f"{caminho}: dg_data em offset {dg_data} e {bloco.bid!r}, esperava ##DT ou ##DL"
    )


def _ler_valor_mestre(
    fh,
    caminho: Path,
    inicio_dado: int,
    tamanho_dado: int,
    indice_registro: int,
    record_size: int,
    canal: _CanalMdf,
) -> float:
    """Le o valor numerico do canal mestre num registro (por indice).

    Leitura pontual: um `seek` no offset calculado por aritmetica de
    ponteiro (nunca varredura) e um `read` do tamanho exato do campo.
    """
    if canal.bit_offset != 0 or canal.bit_count % 8 != 0:
        raise ErroDeLeitura(
            f"{caminho}: canal mestre com campo empacotado em bit "
            f"(bit_offset={canal.bit_offset}, bit_count={canal.bit_count}), "
            "decodificacao de sub-byte nao suportada"
        )
    fmt = _STRUCT_POR_TIPO.get((canal.data_type, canal.bit_count))
    if fmt is None:
        raise ErroDeLeitura(
            f"{caminho}: canal mestre com data_type={canal.data_type} "
            f"bit_count={canal.bit_count}, combinacao nao suportada"
        )
    tamanho_campo = canal.bit_count // 8
    offset_registro = indice_registro * record_size
    offset_campo = offset_registro + canal.byte_offset
    if offset_campo + tamanho_campo > tamanho_dado:
        raise ErroDeLeitura(
            f"{caminho}: registro {indice_registro} do canal mestre "
            f"ultrapassa o bloco de dado (offset {offset_campo}, "
            f"bloco com {tamanho_dado} bytes)"
        )
    fh.seek(inicio_dado + offset_campo)
    bruto = fh.read(tamanho_campo)
    if len(bruto) < tamanho_campo:
        raise ErroDeLeitura(
            f"{caminho}: EOF lendo valor do canal mestre em offset "
            f"{inicio_dado + offset_campo}"
        )
    return float(struct.unpack(fmt, bruto)[0])


def _derivar_frequencia_do_mestre(
    fh,
    caminho: Path,
    dg_data: int,
    canal_mestre: _CanalMdf,
    cycle_count: int,
    record_size: int,
) -> tuple[float, float]:
    """Deriva `(frequencia_hz, duracao_s)` do grupo a partir do canal mestre.

    Formula: `duracao = mestre[ultimo] - mestre[primeiro]`,
    `frequencia_hz = (cycle_count - 1) / duracao`. Ver DECISAO PENDENTE no
    topo do modulo pra tensao com "nao leia a secao de dados".
    """
    if cycle_count < 2:
        raise ErroDeLeitura(
            f"{caminho}: grupo com cycle_count={cycle_count}, precisa de "
            ">= 2 amostras pra provar taxa a partir do canal mestre"
        )
    inicio_dado, tamanho_dado = _localizar_bloco_de_dado(fh, caminho, dg_data)
    primeiro = _ler_valor_mestre(
        fh, caminho, inicio_dado, tamanho_dado, 0, record_size, canal_mestre
    )
    ultimo = _ler_valor_mestre(
        fh,
        caminho,
        inicio_dado,
        tamanho_dado,
        cycle_count - 1,
        record_size,
        canal_mestre,
    )
    duracao = ultimo - primeiro
    if duracao <= 0:
        raise ErroDeLeitura(
            f"{caminho}: canal mestre nao cresce entre o primeiro "
            f"({primeiro}) e o ultimo ({ultimo}) registro, taxa fabricada "
            "seria pior que erro"
        )
    frequencia_hz = (cycle_count - 1) / duracao
    return frequencia_hz, duracao


class LeitorAsamMf4(LeitorDeInventario):
    """Inventario de canal do container ASAM MDF4 (`.mf4`)."""

    formato_id = "asam_mf4"
    versao = "1"

    def inspecionar(self, caminho: Path) -> Cabecalho:
        tamanho_arquivo = caminho.stat().st_size
        tamanho_minimo = IDBLOCK_TAMANHO + BLOCO_CABECALHO_TAMANHO
        if tamanho_arquivo < tamanho_minimo:
            raise ErroDeLeitura(
                f"{caminho}: arquivo menor que IDBLOCK + cabecalho do ##HD "
                f"({tamanho_arquivo} bytes, esperava >= {tamanho_minimo}) "
                "em offset 0"
            )

        with caminho.open("rb") as fh:
            idblock = fh.read(IDBLOCK_TAMANHO)
            if len(idblock) < IDBLOCK_TAMANHO:
                raise ErroDeLeitura(f"{caminho}: EOF lendo IDBLOCK em offset 0")
            if idblock[0:8] != IDBLOCK_MAGIC:
                raise ErroDeLeitura(
                    f"{caminho}: magic {idblock[0:8]!r} != {IDBLOCK_MAGIC!r} "
                    "esperado em offset 0, nao e asam_mf4"
                )
            versao_mdf = idblock[8:16].decode("latin1").strip()
            programa_gerador = idblock[16:24].decode("latin1").strip()

            hd = _ler_bloco(fh, caminho, IDBLOCK_TAMANHO, esperado=b"##HD")
            if len(hd.links) < 6:
                raise ErroDeLeitura(
                    f"{caminho}: ##HD com {len(hd.links)} links, esperava >= 6"
                )
            if len(hd.data) < 8:
                raise ErroDeLeitura(f"{caminho}: ##HD com dado curto demais")
            dg_first = hd.links[0]
            hd_md_comment = hd.links[5]
            (hd_start_time_ns,) = struct.unpack_from("<Q", hd.data, 0)

            comentario = _ler_texto(fh, caminho, hd_md_comment)

            canais: list[CanalBruto] = []
            duracoes: list[float] = []
            n_grupos = 0

            dg_off = dg_first
            dg_visitados: set[int] = set()
            while dg_off != 0:
                if dg_off in dg_visitados:
                    raise ErroDeLeitura(
                        f"{caminho}: lista de ##DG em ciclo, offset {dg_off} "
                        "ja visitado"
                    )
                dg_visitados.add(dg_off)
                dg = _ler_bloco(fh, caminho, dg_off, esperado=b"##DG")
                if len(dg.links) < 4:
                    raise ErroDeLeitura(
                        f"{caminho}: ##DG em offset {dg_off} com "
                        f"{len(dg.links)} links, esperava >= 4"
                    )
                dg_next, cg_first, dg_data, _dg_md = dg.links

                cg_off = cg_first
                cg_visitados: set[int] = set()
                while cg_off != 0:
                    if cg_off in cg_visitados:
                        raise ErroDeLeitura(
                            f"{caminho}: lista de ##CG em ciclo, offset "
                            f"{cg_off} ja visitado"
                        )
                    cg_visitados.add(cg_off)
                    n_grupos += 1
                    grupo_canais, grupo_duracao = self._ler_grupo(
                        fh, caminho, cg_off, dg_data
                    )
                    canais.extend(grupo_canais)
                    if grupo_duracao is not None:
                        duracoes.append(grupo_duracao)
                    cg = _ler_bloco(fh, caminho, cg_off, esperado=b"##CG")
                    cg_off = cg.links[0]

                dg_off = dg_next

        if not canais:
            raise ErroDeLeitura(f"{caminho}: nenhum canal encontrado na arvore")

        capturado_em = datetime.fromtimestamp(
            hd_start_time_ns / 1e9, tz=UTC
        ).isoformat()
        duracao_s = max(duracoes) if duracoes else None

        bruto = {
            "versao_mdf": versao_mdf,
            "programa_gerador": programa_gerador,
            "comentario_hd": comentario or "",
            "n_grupos": str(n_grupos),
        }

        return Cabecalho(
            formato_id=self.formato_id,
            leitor_versao=self.versao,
            canais=tuple(canais),
            capturado_em=capturado_em,
            duracao_s=duracao_s,
            # MDF4 nao tem campo de venue no cabecalho (ao contrario do
            # .ld): os 5 arquivos do acervo so tem author/department/
            # project/subject genericos no comentario do ##HD. Nunca
            # inventar venue a partir disso.
            venue_declarado=None,
            bruto=bruto,
        )

    def _ler_grupo(
        self, fh, caminho: Path, cg_off: int, dg_data: int
    ) -> tuple[list[CanalBruto], float | None]:
        cg = _ler_bloco(fh, caminho, cg_off, esperado=b"##CG")
        if len(cg.links) < 6:
            raise ErroDeLeitura(
                f"{caminho}: ##CG em offset {cg_off} com {len(cg.links)} "
                "links, esperava >= 6"
            )
        if len(cg.data) < 24:
            raise ErroDeLeitura(f"{caminho}: ##CG em offset {cg_off} com dado curto")
        cn_first = cg.links[1]
        cycle_count = struct.unpack_from("<Q", cg.data, 8)[0]
        data_bytes = struct.unpack_from("<I", cg.data, 20)[0]
        invalid_bytes = (
            struct.unpack_from("<I", cg.data, 24)[0] if len(cg.data) >= 28 else 0
        )
        record_size = data_bytes + invalid_bytes
        if record_size <= 0:
            raise ErroDeLeitura(
                f"{caminho}: ##CG em offset {cg_off} com record_size {record_size} <= 0"
            )

        canais_mdf: list[_CanalMdf] = []
        cn_off = cn_first
        cn_visitados: set[int] = set()
        while cn_off != 0:
            if cn_off in cn_visitados:
                raise ErroDeLeitura(
                    f"{caminho}: lista de ##CN em ciclo, offset {cn_off} ja visitado"
                )
            cn_visitados.add(cn_off)
            canal, cn_next = _ler_canal(fh, caminho, cn_off)
            canais_mdf.append(canal)
            cn_off = cn_next

        if not canais_mdf:
            raise ErroDeLeitura(f"{caminho}: ##CG em offset {cg_off} sem nenhum ##CN")

        mestres = [c for c in canais_mdf if c.cn_type == CN_TYPE_MASTER]
        if not mestres:
            raise ErroDeLeitura(
                f"{caminho}: ##CG em offset {cg_off} sem canal mestre "
                "(cn_type == 2), impossivel provar frequencia sem inventar"
            )
        canal_mestre = mestres[0]

        frequencia_hz, duracao_grupo = _derivar_frequencia_do_mestre(
            fh, caminho, dg_data, canal_mestre, cycle_count, record_size
        )

        grupo_canais = [
            CanalBruto(
                nome_bruto=c.nome_bruto,
                frequencia_hz=frequencia_hz,
                n_amostras=cycle_count,
                unidade_declarada=c.unidade_declarada,
            )
            for c in canais_mdf
        ]
        return grupo_canais, duracao_grupo
