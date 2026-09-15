# Medição de cobertura do leitor Pi/Cosworth LISTHEAD `.dat` (2026-09-14)

## Resultado

| item | valor |
|---|---|
| arquivos `.dat` no Drive inteiro (todas as pastas, não só o inventário curado) | 485 |
| arquivos `.dat` no inventário curado (`inventario-telemetria-2026-09-14.tsv`) | 0 |
| amostra medida (sorteio aleatório dos 485) | 20 |
| casaram com a assinatura `LISTHEAD` | 3/20 (15%) |
| identificados como família distinta já catalogada em `formatos.py` | 5/20 (25%) |
| sem formato reconhecido no catálogo atual | 12/20 (60%) |
| dos que casaram com LISTHEAD: abriram sem erro | 3/3 |
| canais declarados (arquivos LISTHEAD) | 48 em todos os 3 |
| canais mapeados (perfil `listhead_dat`) | 7/48 (14,6%) |

## O que foi medido, e por que a amostra veio do Drive inteiro, não do inventário

O TSV curado (`docs/handoff/agy/inventario-telemetria-2026-09-14.tsv`,
commit `b0548b5`) não tem nenhuma linha com extensão `dat`: os 485 arquivos
`.dat` do Drive não entraram na classificação por logger que o Antigravity
fez em 2026-09-14. Isso por si é um achado: a base usada para dimensionar
esta auditoria subestima o volume de `.dat` a tratar. Para medir este
formato, sorteei 20 caminhos direto de `~/.cache/rclone/drive-index.tsv`
(seed 7) filtrando por `.dat`, copiei do Drive e rodei `detectar()` e, para
os que casaram, `LeitorPiListheadDat.inspecionar()`
(`src/saru_poc/readers/pi_listhead_dat.py`).

## Tabela por arquivo

| arquivo | tamanho MB | classificação |
|---|---|---|
| run72_Pressure_12C - Collapsed.dat | 0,420 | não reconhecido (magic `serialization::archive`, boost C++) |
| ac_shaft (2022_12_18 20_23_00 UTC).dat | 0,003 | não reconhecido (ASCII, cabeçalho `$ Exported by ViewFlex`) |
| act.dat | 0,266 | não reconhecido (magic `\x89HDF\r\n`, container HDF5) |
| ds.dat | 17,305 | não reconhecido (ASCII, formato tipo config `/batch ... /config`) |
| bode_phase_thi.dat | 0,004 | não reconhecido (ASCII, série numérica pura) |
| bodeplot_theta.dat | 0,004 | não reconhecido (ASCII, série numérica pura) |
| run31_Pressure_14 - Collapsed.dat | 0,179 | não reconhecido (boost, igual ao run72) |
| Fabio PittaBMW S1000RR18112022 (...).dat | 0,907 | família distinta já catalogada (`NAO_IDENTIFICADO`, prefixo `00 00 00 01`) |
| Danilo BrumKawasaki ZX1019112021.dat | 0,407 | família distinta já catalogada |
| DazziBMW S1000RR21102017_001.dat | 0,211 | família distinta já catalogada |
| Gui Brito4428102021.dat | 0,855 | família distinta já catalogada |
| _P.Piquet000986.dat | 1,482 | LISTHEAD, abriu, 48 canais, 7 mapeados |
| _P.Piquet000989.dat | 0,063 | LISTHEAD, abriu, 48 canais, 7 mapeados |
| _P.Piquet000987.dat | 7,661 | LISTHEAD, abriu, 48 canais, 7 mapeados |

(3 entradas duplicadas por hash na amostra bruta do drive-index foram
descartadas da tabela acima; a contagem 3/20, 5/20, 12/20 do resumo conta
cada caminho sorteado uma vez.)

## O que fica de fora e por quê

Dois problemas distintos, não um só:

1. **Cobertura de canal do LISTHEAD em si**: dos 48 canais declarados pelos
   3 arquivos que abriram, só 7 (14,6%) têm alias no perfil `listhead_dat`
   de `seeds/aliases.yaml`. Não mapeados: `Air Temp`, `Alarm Status`,
   `Battery Voltage`, `Beacon Code`, `Box Temperature`, `Box Voltage`,
   `Brake Press R`, `CPU Usage`, `Can Rx Packets`, `Cumulative Diff`,
   `Cumulative Time`, `Damper FL/FR/RL/RR` e outros (lista completa em
   `resultados.json` do run desta medição). `Damper FL/FR/RL/RR` e
   `Brake Press R` são candidatos óbvios de canônico de suspensão e freio,
   mesma lacuna que `.ld` tem.

2. **Cobertura de detecção do universo `.dat`**: a nota em `formatos.py`
   ("só 25 dos 37 `.dat` do acervo") media contra um lote de 37 arquivos
   reunido em 29/08, não os 485 do Drive inteiro. Nesta amostra de 20 sobre
   os 485, LISTHEAD é minoria (15%). Os outros 85% se dividem em pelo menos
   quatro famílias, nenhuma catalogada em `formatos.py`:
   - HDF5 (`\x89HDF\r\n`), formato genérico de dado científico, não é
     telemetria automotiva reconhecível pelo nome do arquivo (`act.dat`).
   - Arquivo serializado por `boost::serialization` (C++), sufixo
     "Collapsed" no nome, parece saída de simulação estrutural
     (`run72_Pressure_12C`, `run31_Pressure_14`), não telemetria de pista.
   - Exportação ASCII do software ViewFlex (`ac_shaft*.dat`).
   - ASCII solto tipo configuração (`ds.dat`) ou série numérica sem
     cabeçalho (`bode_phase_thi.dat`, `bodeplot_theta.dat`).
   - A família de 12 arquivos de moto já catalogada como
     `NAO_IDENTIFICADO` em `formatos.py` (confirmada de novo nesta amostra:
     4 dos 20 batem no prefixo `00 00 00 01`, nomes com padrão
     `<piloto><moto><data>.dat`).

   Nenhum desses 4 grupos é telemetria de carro de pista (são simulação de
   engenharia, dado de moto ou exportação de outra ferramenta), então não é
   necessariamente uma lacuna de cobertura do domínio Piloto: é uma lacuna
   de **classificação**, que hoje faz `detectar()` devolver "assinatura não
   consta no catálogo" sem indicar se aquilo é lixo ou telemetria não
   catalogada.

Issues abertas para as duas lacunas: ver `docs/cobertura-de-dados-resumo.md`.
