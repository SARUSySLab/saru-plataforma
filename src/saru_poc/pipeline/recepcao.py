"""Etapa 1: recepcao.

Um upload vira 1 `gravacao` e N `arquivo_bruto`. O caso do bundle e a regra,
nao a excecao: o AiM manda .xrk, .drk, .gpk, .rrk e .bak da mesma captura, e o
plano cita o caso F3 com 6 arquivos. Pro caminho CSV o bundle degenera pra 1
arquivo e nada muda.

Nada de amostra e lido aqui. Esta etapa so estabelece rastreabilidade: quem e
o arquivo, que formato os bytes dizem que ele e, e qual e o hash. Ler e da
etapa 2.

Dedupe: a chave natural da gravacao e o sha256 do arquivo primario. Reenviar o
mesmo arquivo devolve a gravacao que ja existe, nunca cria a segunda.
"""

from __future__ import annotations

import hashlib
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

from ..readers import detectar

_CHUNK = 1 << 20

# Quem manda no bundle. O primeiro formato desta ordem que aparecer no conjunto
# vira o primario; os outros pegam o papel da tabela abaixo. Ordem por riqueza
# de canal: quem carrega a amostra vem antes de quem carrega indice ou GPS.
PRIORIDADE_PRIMARIO = (
    "aim_xrk",
    "motec_ld",
    "protune_dlf",
    "bosch_bmsbin",
    "asam_mf4",
    "vbox_vbo",
    "pi_pid",
    "pi_listhead_dat",
    "aim_drk",
    "aim_gpk",
    "aim_rrk",
    "motec_ldx",
)

# Papel de cada formato QUANDO ele nao e o primario do bundle.
PAPEL_SECUNDARIO = {
    "aim_drk": "indice",
    "aim_rrk": "indice",
    "motec_ldx": "indice",
    "aim_gpk": "gps",
}


@dataclass
class ArquivoRecebido:
    caminho: Path
    formato_id: str | None
    papel: str
    sha256: str
    bytes_: int
    confianca: str
    motivo: str
    id: str | None = None


@dataclass
class Recepcao:
    gravacao_id: str
    arquivos: list[ArquivoRecebido] = field(default_factory=list)
    ja_existia: bool = False
    recusados: list[str] = field(default_factory=list)


def sha256_de(caminho: Path) -> str:
    h = hashlib.sha256()
    with caminho.open("rb") as fh:
        for bloco in iter(lambda: fh.read(_CHUNK), b""):
            h.update(bloco)
    return h.hexdigest()


def _papel(formato_id: str | None, caminho: Path, primario: str | None) -> str:
    if caminho.suffix.lower() == ".bak":
        return "backup"
    if formato_id is not None and formato_id == primario:
        return "primario"
    return PAPEL_SECUNDARIO.get(formato_id or "", "backup")


def agrupar_bundles(caminhos: Iterable[Path]) -> list[list[Path]]:
    """Agrupa por pasta e radical do nome: e assim que o AiM nomeia a captura."""
    grupos: dict[tuple[Path, str], list[Path]] = defaultdict(list)
    for c in caminhos:
        grupos[(c.parent, c.stem)].append(c)
    return [sorted(v) for v in grupos.values()]


def receber(conn, caminhos: list[Path], *, label: str | None = None) -> Recepcao:
    """Registra um bundle como 1 gravacao. Idempotente pelo sha do primario."""
    if not caminhos:
        raise ValueError("recepcao sem arquivo")

    lidos: list[ArquivoRecebido] = []
    recusados: list[str] = []
    for c in caminhos:
        d = detectar(c)
        if d.formato is None:
            recusados.append(f"{c.name}: {d.motivo}")
            continue
        lidos.append(
            ArquivoRecebido(
                caminho=c,
                formato_id=d.formato.id,
                papel="",
                sha256=sha256_de(c),
                bytes_=c.stat().st_size,
                confianca=d.confianca,
                motivo=d.motivo,
            )
        )
    if not lidos:
        raise ValueError(
            "nenhum arquivo do bundle tem formato reconhecido. "
            "Recepcao nao adivinha formato: " + "; ".join(recusados)
        )

    presentes = {a.formato_id for a in lidos}
    primario = next((f for f in PRIORIDADE_PRIMARIO if f in presentes), None)
    if primario is None:
        primario = lidos[0].formato_id
    # Exatamente um primario por gravacao: se o bundle tem dois arquivos do
    # mesmo formato campeao, o primeiro em ordem leva, o resto vira backup.
    ja_tem_primario = False
    for a in lidos:
        papel = _papel(a.formato_id, a.caminho, primario)
        if papel == "primario":
            if ja_tem_primario:
                papel = "backup"
            else:
                ja_tem_primario = True
        a.papel = papel

    if not ja_tem_primario:
        # Bundle sem candidato natural a primario: acontece quando o conjunto
        # inteiro cai numa regra secundaria, por exemplo so arquivos `.bak` do
        # AiM, cuja extensao vira `backup` antes da promocao. Toda gravacao
        # precisa de exatamente um primario (indice unique parcial no banco),
        # entao promove o primeiro na ordem de prioridade em vez de falhar.
        ordem = {f: i for i, f in enumerate(PRIORIDADE_PRIMARIO)}
        escolhido = min(
            lidos, key=lambda a: (ordem.get(a.formato_id or "", 99), a.caminho.name)
        )
        escolhido.papel = "primario"

    sha_primario = next(a.sha256 for a in lidos if a.papel == "primario")

    existente = conn.execute(
        """select gravacao_id from arquivo_bruto
           where sha256 = %s and papel = 'primario' limit 1""",
        (sha_primario,),
    ).fetchone()
    if existente:
        # A gravacao ja existe, mas quem chamou precisa dos ids pra reprocessar:
        # ingestao e append-only, entao reenviar o mesmo arquivo e um caso
        # normal, nao um no-op.
        gravacao_id = existente[0]
        por_sha = {
            r[1]: str(r[0])
            for r in conn.execute(
                "select id, sha256 from arquivo_bruto where gravacao_id = %s",
                (gravacao_id,),
            )
        }
        for a in lidos:
            a.id = por_sha.get(a.sha256)
        return Recepcao(str(gravacao_id), lidos, ja_existia=True, recusados=recusados)

    gravacao_id = conn.execute(
        "insert into gravacao (label) values (%s) returning id", (label,)
    ).fetchone()[0]

    for a in lidos:
        linha = conn.execute(
            """insert into arquivo_bruto
                 (gravacao_id, papel, formato_id, nome_arquivo, sha256, bytes,
                  objeto_uri)
               values (%s,%s,%s,%s,%s,%s,%s)
               on conflict (gravacao_id, sha256) do nothing
               returning id""",
            (
                gravacao_id,
                a.papel,
                a.formato_id,
                a.caminho.name,
                a.sha256,
                a.bytes_,
                a.caminho.resolve().as_uri(),
            ),
        ).fetchone()
        a.id = str(linha[0]) if linha else None

    return Recepcao(str(gravacao_id), lidos, recusados=recusados)
