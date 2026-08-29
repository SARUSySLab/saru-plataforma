"""Catalogo de formatos e deteccao por bytes magicos.

O catalogo de entidades e explicito: a identificacao e por assinatura, nao por
extensao. `.dat` aparece no Pi e no ecossistema MoTeC, `.csv` e de todo mundo,
e o `.dlf` esta rotulado como AiM no saru-app quando a evidencia aponta pra
Pro Tune. Extensao e pista, nunca veredito.

Este catalogo NAO declara se existe leitor. Isso e derivado do registro em
`readers/__init__.py` na hora de semear o banco. A versao anterior escrevia
`leitor="nativo"` a mao, e o resultado foi o banco afirmar suporte nativo a
tres formatos AiM que ninguem lia: suporte fabricado dentro do repo que
existe pra matar suporte fabricado. Literal que envelhece vira mentira.

Todas as assinaturas abaixo foram MEDIDAS no acervo em 2026-08-29, calculando
o maior prefixo comum entre os arquivos reais de cada familia. Nenhuma veio de
documentacao ou de memoria. A contagem de cada linha e quantos arquivos do
acervo sustentam aquela assinatura.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

MAX_MAGIC = 256


@dataclass(frozen=True)
class Formato:
    """Uma linha de `formato_telemetria`."""

    id: str
    rotulo: str
    fabricante: str
    extensao_tipica: str
    assinatura: bytes | None
    binario: bool
    # Onde a assinatura comeca. Quase todo formato tem magic no byte 0, mas o
    # `.pds` do Pi Toolbox nao: os 4 primeiros bytes sao um campo de
    # comprimento mais conteudo (fragmento de caminho Windows da estacao que
    # gravou), e o magic estavel nos 47 arquivos esta no offset 4.
    offset_assinatura: int = 0
    # Marcador secundario, obrigatorio quando a assinatura sozinha e generica
    # demais. `<?xml version="1.0"?>` casa com qualquer XML: sem o marcador, um
    # arquivo de licenca .lic virava MoTeC .ldx. Medido, nao suposto.
    marcador: bytes | None = None
    # Quantos arquivos do acervo sustentam a assinatura, e quando foi medido.
    amostras_medidas: int = 0
    nota: str = ""
    aliases_ext: tuple[str, ...] = field(default_factory=tuple)


# Ordem importa: a deteccao devolve o primeiro match, e assinatura mais longa
# vem antes da mais curta pra evitar que um prefixo fraco roube o veredito.
FORMATOS: tuple[Formato, ...] = (
    Formato(
        id="bosch_bmsbin",
        rotulo="Bosch WinDarab",
        fabricante="Bosch",
        extensao_tipica=".bmsbin",
        assinatura=b"Darab v7",
        binario=True,
        amostras_medidas=96,
        nota="Maior dataset do acervo, 920 MB. Nenhum leitor escrito ainda.",
    ),
    Formato(
        id="aim_gpk",
        rotulo="AiM RS2, canal GPS",
        fabricante="AiM",
        extensao_tipica=".gpk",
        assinatura=b"PROV\x00\x01",
        binario=True,
        amostras_medidas=68,
        nota="Sidecar de GPS do bundle AiM. E ele que da coordenada ao kart-guara.",
    ),
    Formato(
        id="aim_rrk",
        rotulo="AiM RS2, run",
        fabricante="AiM",
        extensao_tipica=".rrk",
        assinatura=b"HEAD\x00\x01",
        binario=True,
        amostras_medidas=67,
    ),
    Formato(
        id="aim_xrk",
        rotulo="AiM RaceStudio 3",
        fabricante="AiM",
        extensao_tipica=".xrk",
        assinatura=b"<hCNF\x00",
        binario=True,
        amostras_medidas=66,
        nota="Leitor e biblioteca de terceiro (libxrk), extra opcional do projeto.",
    ),
    Formato(
        id="asam_mf4",
        rotulo="ASAM MDF4",
        fabricante="ASAM",
        extensao_tipica=".mf4",
        assinatura=b"MDF     ",
        binario=True,
        amostras_medidas=5,
    ),
    Formato(
        id="pi_listhead_dat",
        rotulo="Pi / Cosworth, listhead",
        fabricante="Pi Research",
        extensao_tipica=".dat",
        assinatura=b"LISTHEAD",
        binario=True,
        amostras_medidas=25,
        nota="So 25 dos 37 .dat do acervo. Os outros 12 sao familia distinta.",
    ),
    Formato(
        id="vbox_vbo",
        rotulo="VBOX",
        fabricante="Racelogic",
        extensao_tipica=".vbo",
        assinatura=b"File created on ",
        binario=False,
        amostras_medidas=9,
        nota="ASCII. O plano classifica como trivial, entra quando precisar.",
    ),
    Formato(
        id="motec_ldx",
        rotulo="MoTeC, sidecar de voltas",
        fabricante="MoTeC",
        extensao_tipica=".ldx",
        assinatura=b'<?xml version="1.0"?>',
        binario=False,
        marcador=b"<LDXFile",
        amostras_medidas=26,
        nota=(
            "Traz total de voltas e melhor tempo. Acompanha o .ld irmao. O "
            "prefixo XML sozinho e generico: os 26 do acervo tem `<LDXFile` "
            "nos primeiros 256 bytes, e e ele que separa de um .lic."
        ),
    ),
    Formato(
        id="protune_dlf",
        rotulo="Pro Tune TDL (a confirmar)",
        fabricante="Pro Tune (a confirmar)",
        extensao_tipica=".dlf",
        assinatura=b"#V2\r\n#SERIALNUMBER ",
        binario=False,
        amostras_medidas=1,
        nota=(
            "ATRIBUICAO NAO CONFIRMADA. O saru-app rotula como AiM (classe "
            "AimDlfFileDataSource, perfil `aim`), a ADR-0044 infere FuelTech, e o "
            "Manual de Campo conclui Pro Tune TDL por evidencia convergente "
            "(canal `TDL Battery Voltage`, OBD, GPS proprio). O acervo desta "
            "maquina tem 1 arquivo, nao os 81 que o Manual cita. Nao afirmar o "
            "fabricante ate ver a extensao num cartao SD de dash Pro Tune."
        ),
    ),
    Formato(
        id="pi_pid",
        rotulo="Pi / Cosworth, PID",
        fabricante="Pi Research",
        extensao_tipica=".pid",
        assinatura=b"\x01\x20\x03\x23",
        binario=True,
        amostras_medidas=26,
    ),
    Formato(
        id="motec_ld",
        rotulo="MoTeC i2",
        fabricante="MoTeC",
        extensao_tipica=".ld",
        assinatura=b"\x40\x00\x00\x00",
        binario=True,
        amostras_medidas=42,
        nota=(
            "Assinatura FRACA: 4 bytes de baixa entropia. Confirmar com a "
            "extensao e com o sidecar .ldx antes de cravar."
        ),
    ),
    Formato(
        id="aim_drk",
        rotulo="AiM RS2 (indice)",
        fabricante="AiM",
        extensao_tipica=".drk",
        assinatura=b"RD",
        binario=True,
        amostras_medidas=76,
        aliases_ext=(".bak",),
        nota=(
            "Assinatura FRACA: so 2 bytes de prefixo comum entre os 76 do acervo. "
            "74 comecam com `RDX\\x02`, 2 com `RD\\x90\\x01`. Confirmar com extensao. "
            "O `.bak` do bundle AiM e o mesmo container, por isso entra como alias."
        ),
    ),
    Formato(
        id="pi_pds",
        rotulo="Pi Toolbox, dataset",
        fabricante="Pi Research / Cosworth",
        extensao_tipica=".pds",
        # Magic no offset 4, nao no 0: os 4 primeiros bytes sao um campo de
        # comprimento mais conteudo que varia por estacao de trabalho. Medido
        # em 29/08 nos 47 arquivos do acervo, todos com `1a 12 40 f7` em 4.
        assinatura=b"\x1a\x12\x40\xf7",
        offset_assinatura=4,
        binario=True,
        amostras_medidas=47,
        nota=(
            "Segundo maior volume do acervo, 887 MB. Estrutura medida do zero: "
            "nunca existiu leitor de .pds no saru-app. O arquivo grava do fim "
            "pro comeco, com o metadado nos ultimos bytes."
        ),
    ),
)

FORMATOS_POR_ID = {f.id: f for f in FORMATOS}

# Familias vistas no acervo que NAO tem formato identificado. Registrar a
# ignorancia e melhor que chutar: e a mesma regra do B2.
NAO_IDENTIFICADO = {
    b"\x00\x00\x00\x01\x00\x00\x00\x00": (
        "12 arquivos .dat do acervo, familia distinta do LISTHEAD do Pi. "
        "Fabricante desconhecido em 2026-08-29."
    ),
}


@dataclass(frozen=True)
class Deteccao:
    formato: Formato | None
    confianca: str  # alta, baixa, nenhuma
    motivo: str
    magic: bytes = b""

    @property
    def resolvido(self) -> bool:
        return self.formato is not None


def _le_magic(caminho: Path) -> bytes:
    with caminho.open("rb") as fh:
        return fh.read(MAX_MAGIC)


def detectar(caminho: Path) -> Deteccao:
    """Identifica o formato pelos bytes. Nunca devolve default silencioso.

    Quando nao reconhece, devolve `Deteccao(formato=None)` com o motivo. Cabe
    ao chamador perguntar ou recusar, jamais assumir um formato provavel: e o
    mesmo buraco que produziu o B2 no saru-app.
    """
    magic = _le_magic(caminho)
    if not magic:
        return Deteccao(None, "nenhuma", "arquivo vazio")

    ext = caminho.suffix.lower()
    for fmt in FORMATOS:
        if not fmt.assinatura:
            continue
        ini = fmt.offset_assinatura
        if magic[ini : ini + len(fmt.assinatura)] != fmt.assinatura:
            continue
        if fmt.marcador and fmt.marcador not in magic:
            continue
        if True:
            fraca = "FRACA" in fmt.nota
            aceitas = (fmt.extensao_tipica, *fmt.aliases_ext)
            if fraca and ext not in aceitas:
                return Deteccao(
                    fmt,
                    "baixa",
                    (
                        f"assinatura fraca de {fmt.id} casou, mas a extensao "
                        f"{ext or '(nenhuma)'} nao esta em {aceitas}"
                    ),
                    magic,
                )
            return Deteccao(
                fmt,
                "baixa" if fraca else "alta",
                f"assinatura de {fmt.id}" + (" (fraca)" if fraca else ""),
                magic,
            )

    for prefixo, nota in NAO_IDENTIFICADO.items():
        if magic.startswith(prefixo):
            return Deteccao(
                None, "nenhuma", f"familia conhecida sem formato: {nota}", magic
            )

    return Deteccao(None, "nenhuma", "assinatura nao consta no catalogo", magic)
