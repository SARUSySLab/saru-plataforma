"""Mesma captura AiM guardada como `.xrk` e `.xrz` em pastas diferentes (#53).

A regra vem da medicao em `docs/aim-xrk-medicao.md`: o stream do `.xrz`
descomprimido e igual ao `.xrk`, ou prefixo dele. Nome igual so aponta o
candidato; quem decide e o byte.
"""

from __future__ import annotations

import zlib
from pathlib import Path
from urllib.parse import unquote, urlparse

import numpy as np
import pytest

from saru_poc.pipeline.recepcao import mesma_captura_aim, receber
from saru_poc.pipeline.tracado import derivar_volta


def _stream(n: int = 200_000) -> bytes:
    # bytes aleatorios nao comprimem: cortar o zlib pela metade corta o stream
    # pela metade, que e o caso do .xrz truncado do acervo
    return np.random.default_rng(0).bytes(n)


def _gravar(caminho: Path, dados: bytes) -> Path:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_bytes(dados)
    return caminho


def test_xrz_identico_ao_xrk_e_a_mesma_captura(tmp_path) -> None:
    s = _stream()
    xrk = _gravar(tmp_path / "geral" / "c_1123.xrk", s)
    xrz = _gravar(tmp_path / "piloto" / "c_1123.xrz", zlib.compress(s))
    assert mesma_captura_aim(xrk, xrz)


def test_xrk_com_rodape_de_metadados_e_a_mesma_captura(tmp_path) -> None:
    s = _stream()
    rodape = (
        b"<hVTY\x00\x11\x00\x00\x00\x00>Testes genericos<VTY\x00^\x07><hNTE\x00\x00"
    )
    xrk = _gravar(tmp_path / "a" / "s.xrk", s + rodape)
    xrz = _gravar(tmp_path / "b" / "s.xrz", zlib.compress(s))
    assert mesma_captura_aim(xrk, xrz)


def test_xrz_truncado_ainda_e_a_mesma_captura(tmp_path) -> None:
    s = _stream()
    comprimido = zlib.compress(s)
    xrk = _gravar(tmp_path / "a" / "s.xrk", s)
    xrz = _gravar(tmp_path / "b" / "s.xrz", comprimido[: len(comprimido) * 6 // 10])
    assert mesma_captura_aim(xrk, xrz)


def test_conteudo_diferente_com_o_mesmo_nome_nao_e_a_mesma_captura(tmp_path) -> None:
    s = _stream()
    outra = np.random.default_rng(1).bytes(len(s))
    xrk = _gravar(tmp_path / "a" / "s.xrk", s)
    xrz = _gravar(tmp_path / "b" / "s.xrz", zlib.compress(outra))
    assert not mesma_captura_aim(xrk, xrz)


def test_sessao_curta_copiada_inteira_e_a_mesma_captura(tmp_path) -> None:
    """O menor .xrk do catalogo tem 28 KiB: o piso de truncado nao vale aqui."""
    s = _stream(28_000)
    xrk = _gravar(
        tmp_path / "a" / "s.xrk", s + b"<hNTE\x00\x00\x00\x00\x00\x00><NTE\x00\x00\x00"
    )
    xrz = _gravar(tmp_path / "b" / "s.xrz", zlib.compress(s))
    assert mesma_captura_aim(xrk, xrz)


def test_xrz_truncado_quase_vazio_nao_casa_com_nada(tmp_path) -> None:
    s = _stream()
    comprimido = zlib.compress(s)
    xrk = _gravar(tmp_path / "a" / "s.xrk", s)
    xrz = _gravar(tmp_path / "b" / "s.xrz", comprimido[:4096])
    assert not mesma_captura_aim(xrk, xrz)


@pytest.fixture
def conn():
    try:
        from saru_poc.db import connect

        with connect() as c:
            yield c
            c.rollback()
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"postgres indisponivel: {e}")


def test_xrz_em_outra_pasta_entra_como_backup_da_gravacao_do_xrk(
    conn, tmp_path
) -> None:
    linha = conn.execute(
        """select objeto_uri, nome_arquivo from arquivo_bruto
            where formato_id = 'aim_xrk' and papel = 'primario'
              and lower(nome_arquivo) like '%.xrk'
            order by bytes limit 1"""
    ).fetchone()
    if linha is None:
        pytest.skip("catalogo sem .xrk primario")
    origem = Path(unquote(urlparse(linha[0]).path))
    if not origem.exists():
        pytest.skip("arquivo do catalogo fora do disco")
    donas = {
        str(r[0])
        for r in conn.execute(
            """select gravacao_id from arquivo_bruto
                where formato_id = 'aim_xrk' and papel = 'primario'
                  and lower(nome_arquivo) in (lower(%s), lower(%s))""",
            (f"{origem.stem}.xrk", f"{origem.stem}.xrz"),
        )
    }

    copia = _gravar(
        tmp_path / "outra_pasta" / f"{origem.stem}.xrz",
        zlib.compress(origem.read_bytes()),
    )
    rec = receber(conn, [copia])

    assert rec.ja_existia
    assert rec.gravacao_id in donas
    assert [a.papel for a in rec.arquivos] == ["backup"]
    assert rec.copia_de is not None


def test_mesma_captura_em_duas_gravacoes_nao_quebra_o_tracado(conn) -> None:
    """Catalogo ingerido antes da regra de recepcao ja tem as duplicatas."""
    par = conn.execute(
        r"""select a1.gravacao_id, a2.gravacao_id
              from arquivo_bruto a1
              join arquivo_bruto a2
                on a2.formato_id = 'aim_xrk' and a2.papel = 'primario'
               and a1.gravacao_id < a2.gravacao_id
               and regexp_replace(lower(a1.nome_arquivo), '\.xr[kz]$', '')
                 = regexp_replace(lower(a2.nome_arquivo), '\.xr[kz]$', '')
             where a1.formato_id = 'aim_xrk' and a1.papel = 'primario'
               and exists (select 1 from volta v
                            where v.session_id = a1.gravacao_id and v.layout_id is not null)
               and exists (select 1 from volta v
                            where v.session_id = a2.gravacao_id and v.layout_id is not null)
             limit 1"""
    ).fetchone()
    if par is None:
        pytest.skip("catalogo sem a mesma captura em duas gravacoes")

    motivos: list[str] = []
    gravou_primeira = False
    for i, gid in enumerate(par):
        for (vid,) in conn.execute(
            "select id from volta where session_id = %s order by lap_number", (gid,)
        ).fetchall():
            r = derivar_volta(conn, str(vid), rederivar=True)
            gravou_primeira |= i == 0 and r.gravou
            if i == 1:
                motivos.append(r.motivo or "")
    if not gravou_primeira:
        pytest.skip("a primeira gravacao do par nao tem tracado derivavel")
    assert any("mesma captura em outra gravacao" in m for m in motivos)
