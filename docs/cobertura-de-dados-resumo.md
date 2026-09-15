# Cobertura de dado e desempenho dos leitores, exceto `.pds`/`.pid` (2026-09-14)

Auditoria dos leitores em `src/saru_poc/readers/` e do mapa `seeds/aliases.yaml`,
exceto `pi_pds.py` e `pi_pid.py` (já medidos nas issues #25 e #26, com PR #34
e #35 abertos). Fonte de dado: inventário curado do acervo
(`docs/handoff/agy/inventario-telemetria-2026-09-14.tsv`, commit `b0548b5`)
complementado pelo índice bruto do Drive (`~/.cache/rclone/drive-index.tsv`)
para `.dat`, que o inventário curado não classificou. Amostras copiadas do
Drive para scratch local (não versionadas), lidas com os leitores reais via
`uv run python`.

## Tabela consolidada

| formato | arquivos únicos no acervo | arquivos que abriram (amostra) | canais médios declarados | canais médios mapeados | cobertura | tempo médio (MB/s, `inspecionar`) | issues abertas |
|---|---|---|---|---|---|---|---|
| `.xrk` (AiM RS3) | 687 | 10/10 | 32,3 | 7,1 | 22,0% | 34,8 | #37 |
| `.ld` (MoTeC i2) | 116 | 10/10 (5 vazios por desenho) | 18,9 (0 nos vazios) | 1,2 | 6,3% (só arquivos com canal) | não é medida útil (< 1 ms mesmo em 8 MB) | #38 |
| `.ldx` (MoTeC, sidecar) | 34 | 10/10 | 0 (sem canal, por desenho) | não se aplica | não se aplica | não é medida útil | nenhuma |
| `.gpk` (AiM RS2) | 340 | 10/10 | 0 (sem canal decodificável, confirmado) | não se aplica | não se aplica, ver nota | 432,4 | nenhuma (ver nota) |
| `.rrk` (AiM RS2) | 502 | 10/10 | 0 (idem) | não se aplica | não se aplica, ver nota | 239,4 | nenhuma (ver nota) |
| `.drk`/`.bak` (AiM RS2) | 536 | 10/10 | 0 (idem) | não se aplica | não se aplica, ver nota | 392,9 | nenhuma (ver nota) |
| `.vbo` (Racelogic VBOX) | 6 (universo completo) | 6/6 | 34,7 | 11,0 | 31,7% | 93,1 | #41 |
| `.mf4` (ASAM MDF4) | 54 | 4/9 (56% falham) | 1210,5 (só quem abriu) | 0 | 0% (sem perfil no `aliases.yaml`) | 1826,3 (só quem abriu; não mede throughput de amostra) | #40 |
| `.dlf` (`protune_dlf`) | 1 (universo completo) | 1/1 | 138 | 14,0 | 10,1% | 16,4 | nenhuma (amostra=1, ver `docs/protune-dlf-medicao.md`) |
| `.dat` LISTHEAD (Pi) | não determinável do inventário curado (0 linhas); 485 `.dat` no Drive, 15% LISTHEAD na amostra | 3/3 (dos que casaram a assinatura) | 48 | 7,0 | 14,6% | não é medida útil (< 1 ms) | #39 (classificação), #42 (mapa de canal) |

Nota `.gpk`/`.rrk`/`.drk`: `Cabecalho.canais` sai sempre vazio por decisão
medida e documentada em `docs/aim-gpk-rrk-medicao.md` e
`docs/aim-rs2-medicao.md` (a tabela de descritores de canal não decodifica
em nenhum dos 129+68+67 arquivos medidos em 29/08, reconfirmado nesta
auditoria com amostra nova de 30 arquivos adicionais). Não é uma falha do
leitor: é a estrutura do container que não expõe canal decodificável com a
técnica usada até aqui. Por isso não entra na coluna "cobertura" nem gera
issue de mapa de canal; o que falta nesses três formatos é decodificação de
container, tratado como item em aberto nos dois documentos de medição
citados, fora do escopo desta auditoria de cobertura de dado.

## O que foi medido

Para cada formato do escopo: amostra aleatória (seed fixa) de arquivos
únicos por hash do inventário do acervo (10 arquivos por formato, ou o
universo inteiro quando menor que 10), copiada do Drive via `rclone copy
gdrive-rw: ... --files-from`, nunca versionada. Cada arquivo passou por
`readers.formatos.detectar()` e pelo `inspecionar()` do leitor
correspondente, cronometrado. Os `nome_bruto` de canal foram comparados
contra a união das colunas (`col`) do(s) perfil(is) de `seeds/aliases.yaml`
que se aplicam àquele formato. `ler()` também rodou em uma sub-amostra
menor de 1-2 arquivos por formato que declara `suporta_amostra = True`
(`.xrk`, `.ld`, `.vbo`, `.dlf`, `.dat` LISTHEAD), para checar se a leitura
de amostra completa o inventário sem lançar exceção nova.

Documentos individuais por formato, com tabela por arquivo:

- `docs/aim-xrk-medicao.md`
- `docs/motec-ld-medicao.md` (cobre `.ld` e `.ldx`)
- `docs/vbox-vbo-medicao.md`
- `docs/asam-mf4-medicao.md`
- `docs/protune-dlf-medicao.md`
- `docs/pi-listhead-dat-medicao.md`
- Complementos datados de 2026-09-14 ao fim de `docs/aim-gpk-rrk-medicao.md` e `docs/aim-rs2-medicao.md` (já existiam, reconfirmados com amostra nova em vez de reescritos)

## Desempenho

Nenhum leitor do escopo materializa arquivo inteiro em memória de forma
desproporcional ao tamanho típico do formato: `aim_rs2.py` lê o `.drk`/`.gpk`
inteiro com `read_bytes()`, mas o maior arquivo medido do formato é 1,8 MB
(documentado em `docs/aim-rs2-medicao.md`), então o custo é trivial.
`inspecionar()` em `.mf4` decodifica só cabeçalho de canal (`##CN`/`##CG`/
`##DG`), não os blocos de dado: a velocidade aparente (1,2 a 2,1
GB/s) mede o tempo de parsear metadado em arquivo de dezenas de MB, não o
throughput real de leitura de amostra. `.xrk`, `.vbo` e `.dlf` (os três que
rodaram `ler()` além de `inspecionar()`) ficaram entre 3,3 e 40,5 MB/s de
throughput real de amostra na sub-amostra testada; nenhum indício de
complexidade quadrática ou pior nos tempos medidos (tempo cresce
linearmente com o tamanho do arquivo nas tabelas de cada documento). Não
há leitor no escopo desta auditoria comparável em lentidão ao ponto de
justificar issue de desempenho dedicada.

## Issues e documentação

Issues novas desta auditoria, numeradas por impacto (arquivos únicos
afetados no acervo, maior primeiro):

1. **#37**: `.xrk`, cobertura de canal 22% (687 arquivos únicos).
2. **#38**: `.ld`, cobertura de canal 6,3% e falha de `ler()` em canal
   `GPS Heading` real (116 arquivos únicos).
3. **#39**: `.dat`, só 15% são LISTHEAD na amostra do Drive inteiro, resto
   sem catálogo (485 arquivos `.dat` no Drive, volume que o inventário
   curado não capturou).
4. **#40**: `.mf4`, 56% dos arquivos da amostra recusados por
   `dl_count > 1` não suportado (54 arquivos únicos).
5. **#42**: `.dat` LISTHEAD, cobertura de canal 15% (amortecedor, freio),
   dependente da classificação corrigida em #39.
6. **#41**: `.vbo`, cobertura de canal 32% (6 arquivos únicos, prioridade
   baixa por volume).

### Rastreabilidade (requisito e ADR por issue, reaproveitando a matriz de `docs/handoff/caixa-claude.md` R4)

| issue | requisitos | ADR |
|---|---|---|
| #25 | E-RF-01, E-RNF-09, PIL-RF-03, PIL-RNF-05 | ADR-001 |
| #26 | PIL-RF-03, PIL-RF-05, E-RF-01, E-RF-02 | nenhuma citada |
| #27 | E-RNF-01, PIL-RF-13, PIL-RNF-01 | ADR-001, ADR-005 |
| #28 | E-RF-03 | ADR-006, ADR-007 |
| #29 | E-RF-02, PIL-RF-05 | ADR-003 |
| #30 | E-RF-03, PIL-RF-07, PIL-RF-27 | ADR-006 |
| #31 | E-RF-01, PIL-RF-03 | ADR-001 |
| #32 | E-RF-09, PIL-RF-08, PIL-RNF-10 | ADR-007 |
| #33 | E-RF-09 | nenhuma citada |
| #34 | E-RNF-09, PIL-RNF-05 (medição de `.pds`) | ADR-001 |
| #35 | PIL-RF-03, PIL-RF-05 (medição de `.pid`) | ADR-003 |
| #36 | PIL-RF-05 (calibração de zero, `.pid`) | ADR-003 |
| **#37** | PIL-RF-05, PIL-RNF-05, E-RF-02, E-RNF-09 | ADR-003 |
| **#38** | PIL-RF-03, PIL-RF-05, PIL-RF-27, E-RF-01, E-RF-02 | ADR-003 |
| **#39** | PIL-RF-02, E-RF-01 | ADR-001 |
| **#40** | PIL-RF-03, E-RF-01 | ADR-001 |
| **#41** | PIL-RF-05, E-RF-02 | ADR-003 |
| **#42** | PIL-RF-05, E-RF-02 | ADR-003 |

`E-RF-01` (`docs/empresa/requisitos/02-catalogos.md`) já registra "parcial:
12 leitores de logger real, 6 leem amostra completa"; esta auditoria não
muda essa contagem (nenhum leitor novo passou a suportar `ler()`), mas
adiciona evidência de que a cobertura de canal dos 6 que já leem amostra
(`.xrk`, `.ld`, `.vbo`, `.dlf`, `.dat` LISTHEAD, e `.pid`/`.pds` já medidos)
está entre 6% e 32% em quatro deles. `E-RNF-09`/`PIL-RNF-05`
(`docs/requisitos/02-catalogos.md`) registravam "3 de 12 com documento de
medição"; após este PR, 10 de 12 leitores têm documento de medição
(faltam só `pi_pds`/`pi_pid`, que têm medição própria fora deste PR, e
`aim_gpk`/`aim_rrk`/`aim_drk`, que têm medição mas sem canal a cobrir).

## Recomendação de ordem de ataque

**#38 (`.ld`) primeiro.** Critério: é o formato com pior cobertura relativa
entre os que geram issue de mapa de canal (6,3%, contra 22% do `.xrk` e 32%
do `.vbo`), tem volume relevante (116 arquivos únicos, mais que `.vbo` e
`.dlf` juntos) e inclui uma falha de `ler()` reproduzível em arquivo real,
não só lacuna de mapa: corrigi-la desbloqueia tanto cobertura de canal
quanto uma classe de arquivo que hoje nem chega a virar amostra. Em seguida,
**#37 (`.xrk`)** pelo volume (687 arquivos únicos, maior grupo do acervo) e
**#39 (`.dat`)** pelo tamanho da incerteza que resolve (485 arquivos hoje
fora de qualquer classificação). **#40 (`.mf4`)** vem depois: taxa de falha
alta (56%) mas universo pequeno (54 arquivos). **#42** depende de #39.
**#41 (`.vbo`)** por último, volume mínimo.
