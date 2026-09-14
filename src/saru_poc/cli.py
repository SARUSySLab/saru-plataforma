"""CLI da PoC: migrate, doctor e sniff."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

from .config import CONFIG, REPO_ROOT

OK, FALHA, AVISO = "  ok  ", " falha", " aviso"

# Extensoes que o acervo carrega, agrupadas pelo perfil que vai le-las.
# Fonte: Manual de Campo da Telemetria (28/08) + os 21 perfis do aliases.yaml.
FAMILIAS = {
    ".dlf": "Pro Tune TDL (rotulado 'aim' no saru-app, ver ADR-0044)",
    ".xrk": "AiM RaceStudio 3",
    ".drk": "AiM RS2 (indice)",
    ".gpk": "AiM RS2 (GPS)",
    ".rrk": "AiM RS2 (run)",
    ".ld": "MoTeC i2",
    ".ldx": "MoTeC (sidecar de voltas)",
    ".vbo": "VBOX",
    ".dat": "Pi / Cosworth",
    ".pid": "Pi / Cosworth",
    ".csv": "CSV generico (FuelTech, ProTune, TrackAddict, WinDarab, WinTAX)",
    ".mf4": "ASAM MDF4",
    ".bmsbin": "Bosch WinDarab (binario)",
}


def _linha(estado: str, texto: str) -> None:
    print(f"[{estado}] {texto}")


def doctor() -> int:
    falhas = 0
    print("\n== ambiente ==")

    env = REPO_ROOT / ".env"
    if env.exists():
        _linha(OK, f".env presente ({env})")
    else:
        _linha(FALHA, ".env ausente. Rode: cp .env.example .env")
        falhas += 1

    try:
        from .db import ping

        versao = ping().split(",")[0]
        _linha(OK, f"postgres em {CONFIG.pg_host}:{CONFIG.pg_port} -> {versao}")
    except Exception as e:  # noqa: BLE001
        _linha(FALHA, f"postgres inacessivel em {CONFIG.pg_host}:{CONFIG.pg_port}: {e}")
        falhas += 1
    else:
        from .migrate import aplicadas

        aps = aplicadas()
        _linha(OK, f"migrations aplicadas: {len(aps)}")
        for versao, quando in aps:
            print(f"         {versao}  {quando}")

    try:
        CONFIG.parquet_root.mkdir(parents=True, exist_ok=True)
        sonda = CONFIG.parquet_root / ".sonda"
        sonda.write_text("x")
        sonda.unlink()
        _linha(OK, f"parquet root gravavel ({CONFIG.parquet_root})")
    except Exception as e:  # noqa: BLE001
        _linha(FALHA, f"parquet root nao gravavel: {e}")
        falhas += 1

    for lib in ("pyarrow", "duckdb", "numpy", "pandas"):
        try:
            mod = __import__(lib)
            _linha(OK, f"{lib} {getattr(mod, '__version__', '?')}")
        except ImportError:
            _linha(FALHA, f"{lib} ausente")
            falhas += 1
    try:
        import libxrk  # noqa: F401

        _linha(OK, "libxrk presente (leitor nativo AiM .xrk)")
    except ImportError:
        _linha(AVISO, "libxrk ausente. Opcional: uv sync --extra aim")

    print("\n== referencias ==")
    if CONFIG.app_ref.exists():
        _linha(OK, f"snapshot saru-app (so leitura): {CONFIG.app_ref}")
    else:
        _linha(AVISO, f"snapshot saru-app nao encontrado: {CONFIG.app_ref}")

    print("\n== acervo ==")
    if not CONFIG.acervo_root.exists():
        _linha(FALHA, f"acervo nao encontrado: {CONFIG.acervo_root}")
        return falhas + 1

    contagem: Counter[str] = Counter()
    bytes_por_ext: Counter[str] = Counter()
    for f in CONFIG.acervo_root.rglob("*"):
        if not f.is_file() or ".git" in f.parts:
            continue
        ext = f.suffix.lower()
        if ext in FAMILIAS:
            contagem[ext] += 1
            bytes_por_ext[ext] += f.stat().st_size
    _linha(OK, f"acervo em {CONFIG.acervo_root}")
    largura = max((len(FAMILIAS[e]) for e in contagem), default=0)
    for ext, n in contagem.most_common():
        mb = bytes_por_ext[ext] / 1e6
        print(
            f"         {ext:<6} {n:>5} arquivos  {mb:>9.1f} MB  {FAMILIAS[ext]:<{largura}}"
        )
    if not contagem:
        _linha(AVISO, "nenhum arquivo de telemetria reconhecido no acervo")

    print()
    if falhas:
        _linha(FALHA, f"{falhas} problema(s). Ambiente NAO esta pronto.")
    else:
        _linha(OK, "ambiente pronto.")
    return falhas


def inspecionar(caminho: Path) -> int:
    """Le o cabecalho e imprime o inventario de canais. Nao toca no banco.

    E o loop de feedback do trabalho de leitor: roda contra arquivo real e
    mostra o que o parser conseguiu extrair, agrupado por taxa nativa.
    """
    from .readers import detectar, leitor_de

    if not caminho.is_file():
        _linha(FALHA, f"nao e arquivo: {caminho}")
        return 1

    d = detectar(caminho)
    print(f"\n== {caminho.name} ==")
    if d.formato is None:
        _linha(FALHA, f"formato nao reconhecido: {d.motivo}")
        return 1
    _linha(OK, f"formato {d.formato.id} ({d.formato.rotulo}), confianca {d.confianca}")

    leitor = leitor_de(d.formato.id)
    if leitor is None:
        _linha(AVISO, f"sem leitor registrado para {d.formato.id}")
        return 1

    try:
        cab = leitor.inspecionar(caminho)
    except Exception as e:  # noqa: BLE001
        _linha(FALHA, f"{type(e).__name__}: {e}")
        return 1

    _linha(OK, f"leitor {type(leitor).__module__} v{leitor.versao}")
    print(f"         venue declarado : {cab.venue_declarado or '(nao declara)'}")
    print(f"         capturado em    : {cab.capturado_em or '(nao declara)'}")
    dur = f"{cab.duracao_s:.1f} s" if cab.duracao_s else "(nao declara)"
    print(f"         duracao         : {dur}")
    print(f"         canais          : {len(cab.canais)}")

    por_taxa: dict[float, list] = {}
    for c in cab.canais:
        por_taxa.setdefault(c.frequencia_hz, []).append(c)
    for hz in sorted(por_taxa, reverse=True):
        canais = sorted(por_taxa[hz], key=lambda c: c.nome_bruto)
        print(f"\n  {hz:g} Hz  ({len(canais)} canais)")
        for c in canais:
            unidade = c.unidade_declarada or "-"
            faixa = (
                f"  [{c.valor_min:g} .. {c.valor_max:g}]"
                if c.valor_min is not None and c.valor_max is not None
                else ""
            )
            print(
                f"      {c.nome_bruto[:38]:<38} {unidade:<10} {c.n_amostras:>9}{faixa}"
            )

    if cab.bruto:
        print("\n  cabecalho cru")
        for k, v in sorted(cab.bruto.items()):
            print(f"      {k:<26} {str(v)[:70]}")
    return 0


def ingerir_acervo(raiz: Path, formatos: list[str] | None = None) -> int:
    """Passa o acervo inteiro pelas etapas 1 e 2, bundle por bundle.

    Diferente do `amostrar`, que pega uma amostra por formato pra diagnostico,
    este processa tudo. Idempotente: recepcao dedupe por sha256 do primario e
    ingestao e append-only, entao rodar de novo acrescenta historico sem
    duplicar gravacao.
    """
    import time
    from collections import Counter, defaultdict

    from .db import connect
    from .pipeline.ingestao import ingerir
    from .pipeline.recepcao import receber
    from .readers import LEITORES, detectar

    if not raiz.exists():
        _linha(FALHA, f"pasta nao existe: {raiz}")
        return 1

    alvo = set(formatos) if formatos else set(LEITORES)
    desconhecidos = alvo - set(LEITORES)
    if desconhecidos:
        _linha(FALHA, f"sem leitor registrado para {sorted(desconhecidos)}")
        return 1

    print(f"\n== ingestao do acervo ==\n  raiz: {raiz}")
    grupos: dict[tuple, list[Path]] = defaultdict(list)
    n_arq = 0
    for f in sorted(raiz.rglob("*")):
        if not f.is_file() or ".git" in f.parts:
            continue
        d = detectar(f)
        if d.formato and d.formato.id in alvo:
            grupos[(f.parent, f.stem)].append(f)
            n_arq += 1
    _linha(OK, f"{n_arq} arquivo(s) em {len(grupos)} bundle(s)")

    t0 = time.time()
    st: Counter[str] = Counter()
    erros: Counter[str] = Counter()
    series = amostras = 0
    with connect() as conn:
        for _, bundle in sorted(grupos.items()):
            try:
                rec = receber(conn, sorted(bundle))
            except Exception as e:  # noqa: BLE001
                erros[f"recepcao {type(e).__name__}: {str(e)[:60]}"] += 1
                conn.rollback()
                continue
            for a in rec.arquivos:
                if not a.id:
                    continue
                try:
                    r = ingerir(conn, a.id)
                except Exception as e:  # noqa: BLE001
                    erros[f"{a.formato_id} {type(e).__name__}: {str(e)[:60]}"] += 1
                    conn.rollback()
                    continue
                st[r.status] += 1
                series += r.series
                amostras += r.amostras_escritas
                if r.erro:
                    erros[f"{a.formato_id}: {r.erro[:70]}"] += 1
            conn.commit()

    dt = time.time() - t0
    print()
    for status, n in sorted(st.items()):
        _linha(OK, f"{status:<8} {n}")
    _linha(OK, f"series escritas   {series}")
    _linha(OK, f"amostras gravadas {amostras:,}".replace(",", "."))
    _linha(OK, f"tempo             {dt:.0f}s")
    if erros:
        print(f"\n  erros ({sum(erros.values())} ocorrencia(s)):")
        for e, n in erros.most_common(12):
            print(f"    {n:>4}x {e}")
    return 0


def amostrar(raiz: Path) -> int:
    """Uma amostra de cada formato, ponta a ponta pelas etapas 1 e 2.

    Percorre o acervo, escolhe um arquivo por formato detectado, monta o bundle
    dele (mesma pasta, mesmo radical de nome, que e como o AiM nomeia a
    captura) e roda recepcao e ingestao. Formato sem leitor registrado gera
    linha de `ingestao` com status falhou e o motivo, de proposito.
    """
    from .db import connect
    from .pipeline.ingestao import ingerir
    from .pipeline.recepcao import PRIORIDADE_PRIMARIO, receber
    from .readers import detectar

    if not raiz.exists():
        _linha(FALHA, f"pasta nao existe: {raiz}")
        return 1

    print(f"\n== varrendo {raiz} ==")
    por_formato: dict[str, list[Path]] = {}
    for f in sorted(raiz.rglob("*")):
        if not f.is_file() or ".git" in f.parts:
            continue
        d = detectar(f)
        if d.formato is not None:
            por_formato.setdefault(d.formato.id, []).append(f)
    _linha(OK, f"{len(por_formato)} formato(s) presente(s) no acervo")

    ordem = [f for f in PRIORIDADE_PRIMARIO if f in por_formato]
    ordem += [f for f in sorted(por_formato) if f not in ordem]

    cobertos: set[str] = set()
    total_arq = total_ing = 0
    with connect() as conn:
        for formato in ordem:
            if formato in cobertos:
                continue
            escolhido = por_formato[formato][0]
            bundle = sorted(
                f
                for f in escolhido.parent.iterdir()
                if f.is_file() and f.stem == escolhido.stem
            )
            rec = receber(conn, bundle, label=f"amostra {formato}")
            conn.commit()
            marca = " (ja existia)" if rec.ja_existia else ""
            print(f"\n  {formato}{marca}")
            print(f"    gravacao {rec.gravacao_id}  bundle de {len(rec.arquivos)}")
            for a in rec.arquivos:
                cobertos.add(a.formato_id or "")
                total_arq += 1
                print(
                    f"      {a.papel:<9} {a.caminho.name[:46]:<46} "
                    f"{a.formato_id:<16} {a.bytes_ / 1e6:>7.1f} MB  {a.sha256[:8]}"
                )
                if a.id is None:
                    continue
                r = ingerir(conn, a.id)
                conn.commit()
                total_ing += 1
                detalhe = (
                    r.erro
                    if r.erro
                    else (
                        f"{r.canais_lidos} canais, {r.canais_sem_mapa} sem mapa, "
                        f"{r.amostras_escritas} amostras, {r.series} serie(s)"
                    )
                )
                print(f"      {'':<9} -> ingestao {r.status:<8} {detalhe}")
            for x in rec.recusados:
                print(f"      recusado  {x}")

    print(f"\n[  ok  ] {total_arq} arquivo(s) recebido(s), {total_ing} ingestao(oes)")
    return 0


def resolver_pista() -> int:
    """Etapa 4, primeiro degrau da cascata: alias. GPS e pergunta vem depois."""
    from .db import connect
    from .pipeline.resolucao_pista import resolver

    print("\n== resolucao de pista (degraus alias e GPS) ==")
    with connect() as conn:
        r = resolver(conn)
        conn.commit()
    _linha(OK, f"resolvidas          {r.resolvidas}")
    _linha(OK, f"  das quais por GPS {r.por_gps}")
    _linha(OK, f"aliases aprendidos  {r.aliases_novos}")
    _linha(AVISO, f"sem venue declarado {r.sem_venue}")
    _linha(AVISO, f"nao resolvidas      {r.nao_resolvidas}")
    for motivo, n in sorted(r.por_motivo.items(), key=lambda x: -x[1]):
        print(f"         {n:>4}x {motivo}")
    return 0


def seed_pistas() -> int:
    """Transcreve o catalogo de pista do saru-app pro nosso modelo."""
    from .db import connect
    from .pista import caminho_tracks, semear_aliases_curados, semear_pistas

    origem = caminho_tracks()
    if not origem.exists():
        _linha(FALHA, f"tracks.yaml nao encontrado em {origem}")
        return 1
    print("\n== seed do catalogo de pista ==")
    print(f"  fonte: {origem}")
    try:
        with connect() as conn:
            r = semear_pistas(conn)
    except ValueError as e:
        _linha(FALHA, str(e))
        return 1
    _linha(OK, f"pistas            {r.pistas}")
    _linha(OK, f"layouts           {r.layouts}")
    _linha(OK, f"aliases de layout {r.aliases}")
    _linha(OK, f"setores           {r.setores}")
    _linha(OK, f"curvas            {r.curvas}")
    with connect() as conn:
        extras = semear_aliases_curados(conn)
        conn.commit()
    _linha(OK, f"aliases curados   {extras} (de-para aprendido, seeds/alias_layout.csv)")
    _linha(
        AVISO,
        "fase nao populada: o tracks.yaml da 3 pontos por curva (inicio, apex, "
        "fim), que definem 2 intervalos. A fronteira das 3 fases precisa de "
        "decisao do Lucas.",
    )
    return 0


def seed(mapa_versao: str) -> int:
    """Carrega o catalogo de acervo. Idempotente."""
    from .acervo import caminho_aliases, semear
    from .db import connect

    origem = caminho_aliases()
    if not origem.exists():
        _linha(FALHA, f"aliases.yaml nao encontrado em {origem}")
        return 1
    print(f"\n== seed do catalogo de acervo (mapa {mapa_versao}) ==")
    print(f"  fonte: {origem}")
    with connect() as conn:
        r = semear(conn, mapa_versao)
    _linha(OK, f"formatos          {r.formatos}")
    _linha(OK, f"grandezas         {r.grandezas}")
    _linha(OK, f"canais canonicos  {r.canais}")
    _linha(OK, f"perfis de origem  {r.perfis}")
    _linha(OK, f"mapeamentos       {r.mapeamentos}")
    if r.reescritos:
        print(f"\n  freio reescrito pra pressao ({len(r.reescritos)}):")
        for x in r.reescritos:
            print(f"    {x}")
    if r.pulados:
        print(f"\n  perfis pulados ({len(r.pulados)}), sem amostra medida:")
        for x in r.pulados:
            print(f"    {x}")
    return 0


def sniff(caminho: Path, *, resumo: bool = False) -> int:
    """Identifica formato pelos bytes, nunca pela extensao.

    Formato reconhecido sem leitor registrado sai como "sem leitor", nao como
    suportado: leitor sem amostra medida e evidencia fabricada (ADR-0044 D5).
    """
    from .readers import LEITORES, detectar

    if not caminho.exists():
        _linha(FALHA, f"caminho nao existe: {caminho}")
        return 1

    alvos = (
        [caminho]
        if caminho.is_file()
        else sorted(
            f for f in caminho.rglob("*") if f.is_file() and ".git" not in f.parts
        )
    )
    agregado: Counter[str] = Counter()
    conflitos: list[str] = []

    for f in alvos:
        d = detectar(f)
        fid = d.formato.id if d.formato else "NAO IDENTIFICADO"
        agregado[f"{fid}|{d.confianca}"] += 1
        aceitas = (
            (d.formato.extensao_tipica, *d.formato.aliases_ext) if d.formato else ()
        )
        if d.formato and f.suffix.lower() not in aceitas:
            conflitos.append(
                f"{f.name}: extensao {f.suffix} mas bytes de {d.formato.id}"
            )
        if not resumo:
            leitor = "com leitor" if fid in LEITORES else "sem leitor"
            print(f"{f.name:<44} {fid:<20} {d.confianca:<7} {leitor}  {d.motivo}")

    if resumo or len(alvos) > 1:
        print(f"\n== resumo de {len(alvos)} arquivo(s) ==")
        for chave, n in agregado.most_common():
            fid, conf = chave.split("|")
            leitor = "com leitor" if fid in LEITORES else "SEM LEITOR"
            print(f"  {n:>5}x  {fid:<22} confianca={conf:<8} {leitor}")

    if conflitos:
        print(f"\n== extensao x bytes divergem ({len(conflitos)}) ==")
        for c in conflitos[:20]:
            print(f"  {c}")

    nao_id = sum(n for k, n in agregado.items() if k.startswith("NAO IDENTIFICADO"))
    if nao_id:
        print(f"\n[ aviso] {nao_id} arquivo(s) sem formato no catalogo.")
    return 0


def cortar_voltas(*, recortar: bool, detalhe: bool) -> int:
    """Etapa 5: cascata de corte de volta (canal > ldx > gps)."""
    from .db import connect
    from .pipeline.corte_voltas import cortar_todas

    print("\n== corte de voltas ==")
    with connect() as conn:
        resumo, cortes = cortar_todas(conn, recortar=recortar)
        conn.commit()
    _linha(OK, f"gravacoes cortadas  {resumo.cortadas}")
    _linha(OK, f"voltas gravadas     {resumo.voltas}")
    if resumo.ja_cortadas:
        _linha(AVISO, f"ja cortadas         {resumo.ja_cortadas} (use --recortar)")
    _linha(AVISO, f"nao cortadas        {resumo.nao_cortadas}")
    if resumo.por_metodo:
        print("\n  por metodo:")
        for metodo, n in sorted(resumo.por_metodo.items(), key=lambda x: -x[1]):
            print(f"    {n:>4}x {metodo}")
    if resumo.por_taxa:
        print("\n  taxa da serie que cortou (teto da precisao do tempo):")
        for taxa, n in sorted(resumo.por_taxa.items(), key=lambda x: -x[1]):
            print(f"    {n:>4}x {taxa}")
    if resumo.suspeitas:
        print(
            f"\n  {len(resumo.suspeitas)} gravacao(oes) com dispersao de tempo "
            "suspeita (a mais longa vale mais que 3x a mais curta):"
        )
        for gid, razao in sorted(resumo.suspeitas, key=lambda x: -x[1])[:10]:
            print(f"    {gid}  {razao:.1f}x")
    if resumo.por_motivo:
        print("\n  por que nao cortou:")
        for motivo, n in sorted(resumo.por_motivo.items(), key=lambda x: -x[1]):
            print(f"    {n:>4}x {motivo}")
    if detalhe:
        print("\n  detalhe por gravacao cortada:")
        for c in cortes:
            if not c.cortou:
                continue
            tempos = ", ".join(f"{v.tempo_s:.3f}" for v in c.voltas[:6])
            taxa = f"{c.frequencia_hz:g} Hz" if c.frequencia_hz else "-"
            print(
                f"    {c.gravacao_id}  {len(c.voltas):>2} volta(s)  "
                f"{c.metodo_versao:<20} {taxa:>7}  [{tempos}]"
            )
    return 0


def decompor(*, redecompor: bool, detalhe: bool) -> int:
    """Etapa 6: tempo por trecho, contra os setores e curvas do layout."""
    from .db import connect
    from .pipeline.decomposicao import decompor_todas

    print("\n== decomposicao (tempo por trecho) ==")
    with connect() as conn:
        resumo, saidas = decompor_todas(conn, redecompor=redecompor)
        conn.commit()
    _linha(OK, f"voltas decompostas  {resumo.decompostas}")
    _linha(OK, f"trechos gravados    {resumo.trechos}")
    if resumo.ja_decompostas:
        _linha(AVISO, f"ja decompostas      {resumo.ja_decompostas} (use --redecompor)")
    _linha(AVISO, f"nao decompostas     {resumo.nao_decompostas}")
    if resumo.por_origem:
        print("\n  eixo de distancia veio de:")
        for origem, n in sorted(resumo.por_origem.items(), key=lambda x: -x[1]):
            print(f"    {n:>4}x {origem}")
    if resumo.fatores:
        f = resumo.fatores
        print(
            f"\n  fator de fechamento: min {min(f):.3f}  "
            f"mediana {sorted(f)[len(f) // 2]:.3f}  max {max(f):.3f}"
        )
    if resumo.por_motivo:
        print("\n  por que nao decompos:")
        for motivo, n in sorted(resumo.por_motivo.items(), key=lambda x: -x[1]):
            print(f"    {n:>4}x {motivo}")
    if detalhe:
        print("\n  detalhe das voltas decompostas:")
        for d in saidas:
            if not d.decompos:
                continue
            print(
                f"    volta {d.numero:>2}  {d.setores} setor(es) + {d.curvas} curva(s)"
                f"  eixo {d.dist_origem:<10} fator {d.dist_fator:.3f}"
            )
    return 0


def tracar(*, rederivar: bool, detalhe: bool) -> int:
    """Etapa 6, segunda parte: tracado medido de cada volta, do GPS."""
    from .db import connect
    from .pipeline.tracado import derivar_todos

    print("\n== tracado medido ==")
    with connect() as conn:
        resumo, saidas = derivar_todos(conn, rederivar=rederivar)
        conn.commit()
    _linha(OK, f"tracados gravados   {resumo.gravados}")
    _linha(OK, f"subtracados         {resumo.subtracados}")
    if resumo.ja_gravados:
        _linha(AVISO, f"ja derivados        {resumo.ja_gravados} (use --rederivar)")
    _linha(AVISO, f"nao gravados        {resumo.nao_gravados}")
    if resumo.por_motivo:
        print("\n  por que nao gravou:")
        for motivo, n in sorted(resumo.por_motivo.items(), key=lambda x: -x[1]):
            print(f"    {n:>4}x {motivo}")
    if detalhe:
        for r in saidas:
            if r.gravou:
                print(
                    f"    volta {r.numero:>2}  {r.n_pontos} pontos, "
                    f"{r.subtracados} subtracado(s), fator {r.fator:.3f}"
                )
    return 0


def reingerir(*, gravacao: str | None, tudo: bool, desatualizadas: bool = False) -> int:
    """Reprocessa ingestao que ficou pra tras, etapas 2 a 6, igual upload novo.

    Contexto do bug: em producao, `Path.replace` (storage.py e
    pipeline/tracado.py) caia com `OSError: Invalid cross-device link` quando
    origem e destino ficavam em filesystems diferentes. A causa ja foi
    corrigida (virou `shutil.move`), mas a linha de `ingestao` que registrou o
    fracasso continua status='falhou' pra sempre: `ingestao` e append-only por
    desenho (nunca reescreve o passado). E a recepcao dedupe por sha256 do
    arquivo primario, entao reenviar o mesmo arquivo devolve `ja_existia` e
    NAO chama `ingerir` de novo. Sem este comando, o arquivo fica preso.

    Por que precisa limpar volta/tempo_trecho/tracado antes de reingerir, e so
    esses: `ingerir()` (pipeline/ingestao.py) e idempotente por conta propria,
    escreve linha nova em `ingestao` (append-only, correto) e faz
    `on conflict do update` em `canal_gravado`/`on conflict do nothing` em
    `serie_amostral`, entao chamar de novo nao duplica nada ali. O problema e
    downstream: `cortar()` (pipeline/corte_voltas.py) SO recorta se
    `recortar=True` quando ja existe volta pra aquela gravacao, e o arquivo que
    acabou de reingerir pode trazer um canal que a corte anterior nao tinha
    (ex.: o `.xrk` falhou mas o `.drk` irmao ja tinha cortado por GPS; agora
    o contador de volta do `.xrk` manda na cascata e produz corte diferente).
    Manter a volta antiga seria empatar com o resultado de um pipeline
    incompleto, nao com o de um upload novo, que e o que a tarefa pede. E
    `tempo_trecho`/`tracado` (+`subtracado`) referenciam `volta` por FK SEM
    cascade (decisao do catalogo, 28/08: tabela de auditoria/derivado nao pode
    perder historico em cascade silencioso), entao apagar `volta` sem apagar
    os dois antes quebra com violacao de FK. A ordem abaixo (subtracado ->
    tracado -> tempo_trecho -> volta) e a unica que passa pelas FKs.

    O escopo do apagamento e so a(s) gravacao(oes) atingidas pelo arquivo que
    falhou, nunca o catalogo inteiro: `where session_id = %s` em cada delete.
    Gravacao e arquivo_bruto em si nunca sao apagados, so o que os proximos
    passos regravam.
    """
    from .db import connect
    from .pipeline.corte_voltas import cortar
    from .pipeline.decomposicao import decompor_volta
    from .pipeline.ingestao import ingerir
    from .pipeline.resolucao_pista import resolver
    from .pipeline.tracado import derivar_volta

    status_alvo = {"falhou", "parcial"} if tudo else {"falhou"}
    if desatualizadas:
        # Reprocessa TAMBEM o que esta `ok` mas foi lido por versao mais velha
        # do leitor registrado hoje. E o unico criterio honesto pra reprocessar
        # `ok`: "ok" continua sendo ok, o que mudou foi o leitor (ex.: decode
        # tipado fp16 de 29/08, que corrige o VALOR de canais que a versao
        # anterior lia como int16). O filtro por versao acontece abaixo, na
        # selecao, porque depende do formato de cada arquivo.
        status_alvo = status_alvo | {"ok"}

    print("\n== reingestao ==")
    with connect() as conn:
        if gravacao:
            linhas = conn.execute(
                """select distinct on (i.arquivo_id) i.arquivo_id, i.gravacao_id, i.status
                     from ingestao i
                    where i.gravacao_id = %s
                    order by i.arquivo_id, i.iniciada_em desc, i.id desc""",
                (gravacao,),
            ).fetchall()
        else:
            linhas = conn.execute(
                """select distinct on (i.arquivo_id) i.arquivo_id, i.gravacao_id, i.status
                     from ingestao i
                    order by i.arquivo_id, i.iniciada_em desc, i.id desc"""
            ).fetchall()

        if desatualizadas:
            from .readers import LEITORES

            versao_atual = {fmt: le.versao for fmt, le in LEITORES.items()}
            versoes = dict(
                conn.execute(
                    """select distinct on (i.arquivo_id) i.arquivo_id,
                              (i.leitor_versao, a.formato_id)
                         from ingestao i join arquivo_bruto a on a.id = i.arquivo_id
                        order by i.arquivo_id, i.iniciada_em desc, i.id desc"""
                ).fetchall()
            )

            def _desatualizada(arquivo_id, status) -> bool:
                if status != "ok":
                    return True  # falhou/parcial ja entram pelo status_alvo
                par = versoes.get(arquivo_id)
                if par is None:
                    return False
                leitor_versao, formato_id = par
                atual = versao_atual.get(formato_id)
                return atual is not None and leitor_versao != atual

            alvos = [
                (str(arquivo_id), str(gravacao_id))
                for arquivo_id, gravacao_id, status in linhas
                if status in status_alvo and _desatualizada(arquivo_id, status)
            ]
        else:
            alvos = [
                (str(arquivo_id), str(gravacao_id))
                for arquivo_id, gravacao_id, status in linhas
                if status in status_alvo
            ]

        if not alvos:
            _linha(AVISO, "nenhuma ingestao falhou/parcial pra reprocessar")
            return 0

        _linha(OK, f"{len(alvos)} arquivo(s) marcado(s) pra reingerir")

        gravacoes = sorted({g for _, g in alvos})
        for gid in gravacoes:
            conn.execute(
                """delete from subtracado where tracado_id in
                     (select id from tracado where volta_id in
                        (select id from volta where session_id = %s))""",
                (gid,),
            )
            conn.execute(
                """delete from tracado where volta_id in
                     (select id from volta where session_id = %s)""",
                (gid,),
            )
            conn.execute(
                """delete from tempo_trecho where volta_id in
                     (select id from volta where session_id = %s)""",
                (gid,),
            )
            conn.execute("delete from volta where session_id = %s", (gid,))
        conn.commit()

        falharam_de_novo = 0
        for arquivo_id, _ in alvos:
            r = ingerir(conn, arquivo_id)
            conn.commit()
            if r.status == "falhou":
                falharam_de_novo += 1

        # Etapas 4 a 6, mesma sequencia e ordem de `_rodar_pipeline` (api.py),
        # pro resultado sair identico ao de um upload novo.
        resolver(conn)
        conn.commit()

        n_voltas = n_trechos = 0
        for gid in gravacoes:
            cortar(conn, gid)
            conn.commit()
            voltas = [
                str(r[0])
                for r in conn.execute(
                    "select id from volta where session_id = %s order by lap_number",
                    (gid,),
                ).fetchall()
            ]
            for volta_id in voltas:
                decompor_volta(conn, volta_id)
                derivar_volta(conn, volta_id)
            conn.commit()
            n_voltas += len(voltas)
            n_trechos += conn.execute(
                """select count(*) from tempo_trecho t join volta v on v.id = t.volta_id
                    where v.session_id = %s""",
                (gid,),
            ).fetchone()[0]

    _linha(OK, f"reprocessados         {len(alvos)}")
    if falharam_de_novo:
        _linha(FALHA, f"voltaram a falhar     {falharam_de_novo}")
    else:
        _linha(OK, "voltaram a falhar     0")
    _linha(OK, f"gravacoes atingidas   {len(gravacoes)}")
    _linha(OK, f"voltas no fim         {n_voltas}")
    _linha(OK, f"trechos no fim        {n_trechos}")
    return 1 if falharam_de_novo else 0


def emitir_relatorio(
    gravacao_id: str,
    *,
    volta: int | None,
    referencia: int | None,
    fixture: bool,
    saida: str | None,
) -> int:
    """Etapa 7: monta o relatorio, valida contra o contrato do front e emite."""
    import json

    from .contrato import carregar, validar
    from .db import connect
    from .relatorio import amostras, montar

    print("\n== relatorio (etapa 7) ==")
    tipos = carregar()
    with connect() as conn:
        try:
            rel = montar(conn, gravacao_id, volta=volta, referencia=referencia)
        except ValueError as e:
            _linha(FALHA, str(e))
            return 1
        series = {}
        alvos: list[int | str] = [v["n"] for v in rel["n1"]["voltas"]]
        alvos.append("media")
        for alvo in alvos:
            try:
                series[alvo] = amostras(conn, gravacao_id, alvo)
            except ValueError as e:
                _linha(AVISO, f"amostra da volta {alvo}: {e}")
        conn.rollback()

    erros = validar(rel, "Relatorio", tipos)
    for alvo, serie in series.items():
        erros += [f"volta {alvo}: {x}" for x in validar(serie, "SerieAmostras", tipos)]

    if erros:
        _linha(FALHA, f"{len(erros)} divergencia(s) contra o contrato do front")
        for e in erros[:15]:
            print(f"         {e}")
        return 1
    _linha(OK, "bate com o contrato do front (Relatorio + SerieAmostras)")

    mv = rel["n0"]["melhor_volta"]
    _linha(OK, f"voltas              {len(rel['n1']['voltas'])}")
    _linha(
        OK,
        f"melhor volta        {mv['melhor_volta_s']:.3f} s (volta {mv['melhor_volta_n']})",
    )
    if mv["ideal_suprimida"]:
        _linha(AVISO, "volta ideal         suprimida (guarda do B1)")
    else:
        _linha(OK, f"volta ideal         {mv['volta_ideal_s']:.3f} s")
    for rotulo, bloco in (
        ("perdas top 3", rel["n0"]["perdas_top3"]),
        ("n2 por curva", rel["n2"]["por_curva"]),
        ("n2 micro-setor", rel["n2"]["por_micro_setor"]),
        ("trechos", rel["trechos"]),
        ("tracado", rel["tracado"]),
        ("consumo etapa", rel["n1"]["consumo"]["media_etapa"]),
        ("contexto sessao", rel["contexto"]["sessao"]),
    ):
        if bloco.get("disponivel"):
            n = len(bloco.get("itens") or bloco.get("pontos") or [])
            _linha(OK, f"{rotulo:<19} {n} item(ns)")
        else:
            _linha(AVISO, f"{rotulo:<19} degradado: {bloco['motivo']}")
    _linha(OK, f"amostras            {len(series)} serie(s) de {900} pontos")

    if saida:
        Path(saida).write_text(json.dumps(rel, ensure_ascii=False, indent=2))
        _linha(OK, f"gravado em          {saida}")
    if fixture:
        raiz = CONFIG.data_root.parent / "web" / "src" / "fixtures"
        (raiz / "relatorio.json").write_text(
            json.dumps(rel, ensure_ascii=False, indent=2)
        )
        pasta = raiz / "amostras"
        for antigo in pasta.glob("volta-*.json"):
            antigo.unlink()
        for alvo, serie in series.items():
            (pasta / f"volta-{alvo}.json").write_text(
                json.dumps(serie, ensure_ascii=False)
            )
        _linha(OK, f"fixture do front    {raiz} (relatorio + {len(series)} amostras)")
        _linha(
            AVISO,
            "atencao: `npm run dev` roda `npm run fixture` antes de subir e "
            "sobrescreve isto com o sintetico. Use `npx vite` pra ver o dado real.",
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="saru-poc", description="PoC core SARU - track day"
    )
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("migrate", help="aplica as migrations pendentes")
    sub.add_parser("doctor", help="confere o ambiente e inventaria o acervo")
    isp = sub.add_parser(
        "inspecionar", help="le o cabecalho de um arquivo, sem tocar no banco"
    )
    isp.add_argument("caminho")
    ia = sub.add_parser(
        "ingerir-acervo", help="recebe e ingere TODO arquivo com leitor registrado"
    )
    ia.add_argument("raiz", nargs="?", default=None)
    ia.add_argument(
        "--formato", action="append", help="limita a um formato (repetivel)"
    )
    am = sub.add_parser(
        "amostrar", help="recebe e ingere uma amostra de cada formato do acervo"
    )
    am.add_argument("raiz", nargs="?", default=None, help="pasta (default: acervo)")
    sub.add_parser(
        "resolver-pista", help="etapa 4: resolve layout pelo venue declarado"
    )
    cv = sub.add_parser(
        "cortar-voltas", help="etapa 5: corta voltas por canal, ldx ou GPS"
    )
    cv.add_argument(
        "--recortar",
        action="store_true",
        help="apaga as voltas ja gravadas e corta de novo",
    )
    cv.add_argument(
        "--detalhe", action="store_true", help="lista os tempos de cada gravacao"
    )
    dc = sub.add_parser(
        "decompor", help="etapa 6: tempo por trecho contra os setores do layout"
    )
    dc.add_argument(
        "--redecompor",
        action="store_true",
        help="apaga os tempos de trecho ja gravados e refaz",
    )
    dc.add_argument("--detalhe", action="store_true", help="lista volta por volta")
    tr = sub.add_parser(
        "tracar", help="etapa 6: deriva o tracado medido de cada volta, do GPS"
    )
    tr.add_argument(
        "--rederivar", action="store_true", help="apaga o tracado gravado e refaz"
    )
    tr.add_argument("--detalhe", action="store_true", help="lista volta por volta")
    rg = sub.add_parser(
        "reingerir",
        help="reprocessa ingestao que falhou (arquivo preso por causa ja corrigida)",
    )
    rg.add_argument(
        "--gravacao", default=None, help="limita o reprocessamento a uma gravacao (uuid)"
    )
    rg.add_argument(
        "--tudo",
        action="store_true",
        help="reprocessa tambem ingestao parcial, nao so falhou",
    )
    rg.add_argument(
        "--desatualizadas",
        action="store_true",
        help=(
            "reprocessa tambem ingestao ok cujo leitor mudou de versao desde "
            "entao (combine com --tudo pra cobrir falhou+parcial+ok)"
        ),
    )
    rl = sub.add_parser(
        "relatorio", help="etapa 7: monta o relatorio e valida contra o contrato"
    )
    rl.add_argument("gravacao_id")
    rl.add_argument("--volta", type=int, default=None, help="volta em escopo")
    rl.add_argument("--referencia", type=int, default=None, help="volta de referencia")
    rl.add_argument("--saida", default=None, help="grava o JSON neste caminho")
    rl.add_argument(
        "--fixture",
        action="store_true",
        help="grava como fixture do front (web/src/fixtures)",
    )
    sp = sub.add_parser(
        "seed-pistas", help="popula pista, layout, setor e curva do tracks.yaml"
    )
    sp.set_defaults(_noop=None)
    sd = sub.add_parser("seed", help="popula o catalogo de acervo do aliases.yaml")
    sd.add_argument("--mapa", default="2026.08-1", help="versao do mapa de canais")
    sn = sub.add_parser("sniff", help="identifica formato por bytes magicos")
    sn.add_argument("caminho", help="arquivo ou pasta")
    sn.add_argument(
        "--resumo", action="store_true", help="agrega por formato em vez de listar"
    )
    args = p.parse_args(argv)

    if args.cmd == "migrate":
        from .migrate import run

        print("\n== migrations ==")
        run()
        return 0
    if args.cmd == "doctor":
        return 1 if doctor() else 0
    if args.cmd == "inspecionar":
        return inspecionar(Path(args.caminho))
    if args.cmd == "ingerir-acervo":
        return ingerir_acervo(
            Path(args.raiz) if args.raiz else CONFIG.acervo_root, args.formato
        )
    if args.cmd == "amostrar":
        return amostrar(Path(args.raiz) if args.raiz else CONFIG.acervo_root)
    if args.cmd == "resolver-pista":
        return resolver_pista()
    if args.cmd == "cortar-voltas":
        return cortar_voltas(recortar=args.recortar, detalhe=args.detalhe)
    if args.cmd == "decompor":
        return decompor(redecompor=args.redecompor, detalhe=args.detalhe)
    if args.cmd == "tracar":
        return tracar(rederivar=args.rederivar, detalhe=args.detalhe)
    if args.cmd == "reingerir":
        return reingerir(
            gravacao=args.gravacao, tudo=args.tudo, desatualizadas=args.desatualizadas
        )
    if args.cmd == "relatorio":
        return emitir_relatorio(
            args.gravacao_id,
            volta=args.volta,
            referencia=args.referencia,
            fixture=args.fixture,
            saida=args.saida,
        )
    if args.cmd == "seed-pistas":
        return seed_pistas()
    if args.cmd == "seed":
        return seed(args.mapa)
    if args.cmd == "sniff":
        return sniff(Path(args.caminho), resumo=args.resumo)
    return 2


if __name__ == "__main__":
    sys.exit(main())
