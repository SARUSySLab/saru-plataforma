# Medição de cobertura do leitor `.dlf` (perfil `protune_dlf`, 2026-09-14)

## Resultado

| item | valor |
|---|---|
| arquivos únicos no acervo (hash) | 1 (mesmo arquivo aparece 2 vezes: original e cópia em `_QUARENTENA`) |
| abriu sem erro | sim |
| canais declarados | 138 |
| canais mapeados (perfis `protune` + `aim` de `seeds/aliases.yaml`) | 14 (10,1%) |
| tempo `inspecionar()` | 0,49 s para 7,98 MB (16,4 MB/s) |
| tempo `ler()` | 2,42 s para 7,98 MB (3,3 MB/s) |

## O que foi medido

O único `.dlf` do acervo inteiro (`Trabalho/SARU/SaruSys-dados/samples/
amg_cup_a45.dlf`), copiado do Drive e passado por `detectar()`,
`LeitorDlf.inspecionar()` e `LeitorDlf.ler()`
(`src/saru_poc/readers/dlf.py`). `ler()` devolveu 85.406 linhas somadas em
todos os lotes, sem erro.

A atribuição de fabricante deste formato segue **não confirmada**
(`formatos.py`, nota do formato `protune_dlf`): o saru-app rotula como AiM,
outra fonte infere FuelTech, e a convergência de evidência aponta Pro Tune
TDL. Esta medição não resolve a atribuição, só mede cobertura de canal
contra os dois perfis de `aliases.yaml` que hoje apontam para este container
(`protune` e `aim`).

## O que fica de fora e por quê

Canais não mapeados (lista truncada às 15 primeiras em ordem alfabética):
`Ambient Air Temperature`, `Analog Input 1` a `8`, `Barometric Pressure`,
`Best Lap`, `Chronometer Current Time`, `Chronometer Final Time`,
`Chronometer Partial Time`, `Current Time`. A maior parte são canais
auxiliares de aquisição (entradas analógicas genéricas, cronômetro,
temperatura ambiente) que não têm equivalente óbvio no vocabulário canônico
de física veicular do domínio.

**Não abro issue de cobertura dedicada para este formato.** Com um único
arquivo no acervo inteiro, qualquer conclusão sobre "cobertura típica" seria
amostra de tamanho 1, o oposto do padrão de evidência desta auditoria
(mínimo de dois arquivos reais convergentes antes de decisão técnica, regra
global de operação). Se mais `.dlf` entrarem no acervo, refazer esta medição
antes de priorizar o mapa de canal.
