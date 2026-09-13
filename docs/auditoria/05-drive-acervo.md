# Auditoria do acervo SARU no Drive

Data: 2026-09-12. Só leitura, a partir de `~/.cache/rclone/drive-index.tsv` (35787 linhas) e
de `git ls-tree` do clone parcial `_arquivo/dados_telemetria`. Nada foi movido nem apagado.

Limite da comparação com o repositório: o clone é parcial (`blob:none`), então o tamanho em
bytes só está disponível para 212 dos 917 caminhos versionados. A comparação por nome de
arquivo cobre tudo; a comparação por tamanho só esses 212. Hash não foi comparado.

## A. Trabalho/SARU (354 arquivos, 757 MB)

O total do cabeçalho vem do índice (`grep` do prefixo). As linhas de subpasta são inclusivas:
uma pasta filha listada à parte (ex.: `notas/archive_2026-07`) já está contada na mãe, então a
soma das linhas passa do total.

| Subpasta | Arquivos | MB | Período | Tipo | Tema | Importância | Destino proposto |
|---|---|---|---|---|---|---|---|
| 01_ Saru-KB (sem notas e 01_References) | 193 | 20,1 | 2021-11 a 2026-07 | md, py, sh, docx | Espelho do repositório saru-KB | Média, já versionado | Nenhuma ação após confirmar que bate com o git |
| 01_ Saru-KB/01_References | 39 | 97,9 | 2021-11 a 2026-07 | pdf, docx, pptx | Papers e guias (ROADVIEW, sine with dwell, lap time optimisation) | Alta, provável fora do git | docs/referencias do repositório da empresa |
| 01_ Saru-KB/notas | 26 | 18,0 | 2025-09 a 2026-09 | md, html | Plano da PoC, pesquisa RealDash, auditoria de pacotes, catálogo de entidades | Alta, produção recente e única | docs/notas da PoC ou do repositório da empresa |
| 01_ Saru-KB/notas/archive_2026-07 | 3 | 17,3 | 2025-09 a 2026-07 | mp4, docx | 1 vídeo e 2 docx órfãos | Baixa | Quarentena se confirmado obsoleto |
| 03_Marketing | 57 | 23,7 | 2025-05 a 2026-09 | png, md | Espelho do repositório de marketing (CLAUDE.md, SPM.md, logos) | Baixa como dado; contém 1 segredo | Quarentena para `.env` e `logs/`; resto fica como marca |
| SaruSys-dados/resgate_lixeira_toshiba | 6 | 458,7 | 2026-07-25 | exe, rar | Instaladores RaceCon (3 versões) e um rar duplicado | Baixa | Quarentena, manter 1 instalador mais novo |
| SaruSys-dados/samples | 4 | 31,2 | 2024-08 a 2026-07 | ld, dlf | Fixtures MoTeC e AMG, batem por nome com dados_telemetria | Alta | dados_telemetria |
| SaruSys-dados/saru-docs | 17 | 0,8 | 2026-08 | md | Pesquisa bruta: pneu, moto, TPMS, benchmark de UI | Alta, única | docs/pesquisa do repositório da empresa |
| ferramentas/export_pi_validacao | 10 | 118,8 | 2026-08-31 | csv, py | `pds_reader.py` e exports de validação PI Toolbox de sessão real | Alta, ativo agora | Script para a PoC; CSVs como fixture em dados_telemetria |
| Logos teste SARU (raiz) | 1 | 0,7 | 2026-09-07 | sem extensão | Teste de logo | Baixa | Área de marca |

Problemas: `03_Marketing/.env` é segredo solto no Drive. `RaceCon/RaceCon/` é pasta duplicada
dentro de si mesma. `03_Marketing/logs/transcript_backups/*.jsonl` guarda transcrições de
sessão de agente, revisar antes de compartilhar.

## B. Estudo/Apuama/Historico_SARU_KB (763 arquivos, 967 MB), CAD fora

Total do cabeçalho pelo índice. As linhas abaixo não somam 763 porque `Projeto Trainee` tem
381 arquivos no total e só `Tyre` e `sobras_restos` estão listadas, e porque os 4 CAD soltos
ficam fora da linha de CAD.

| Subpasta | Arquivos sem CAD | MB | Período | Tipo | Tema | Importância | Destino proposto |
|---|---|---|---|---|---|---|---|
| Apuama/TIRE | 46 | 180,3 | 2024-03 a 2024-07 | mlx, png, mat | Ensaio de pneu TTC: atrito, resistência de rolamento, carga vertical | Alta | docs/fisica/pneu do repositório da empresa |
| Apuama/VD_NOVO | 17 | 25,1 | 2018 e 2024-08 | xlsx, mlx, pdf | Balanceamento de peso, seminário OptimumG sobre K&C e downforce | Alta, referência difícil de achar de novo | docs/referencias |
| Apuama/VD_antigo | 250 | 58,7 | 2019-07 a 2024-08 | m, mat, png | Modelos MATLAB antigos de dinâmica veicular e suspensão | Média | docs/fisica/dinamica-veicular, revisar antes |
| Apuama/VD_antigo.zip | 1 | 398,5 | 2024-05 | zip | Zip maior que a pasta extraída, pode ter outra versão | Baixa até comparar | Comparar; quarentena se igual |
| Apuama/Projeto Trainee/Tyre | 249 | dentro dos 57,5 do Trainee | 2022-04 a 2024-08 | mlx, mat | Magic Formula, Bill Cobb, GUI de comparação | Média a alta, pode repetir TIRE | Checar sobreposição com TIRE |
| Apuama/Projeto Trainee/sobras_restos | 114 | incluído | 2024-03 | mlx | Rascunhos descartados pelo nome | Baixa | Quarentena |
| Apuama/DT's (2 pdf) | 2 | 0,1 | 2023 | pdf | Desenho técnico | Baixa | Quarentena ou referência dimensional |
| Apuama/ARB | 3 | 0,1 | 2024-10 | mlx | Barra estabilizadora | Média | docs/fisica/dinamica-veicular |
| Engenharia_CAD e 4 CAD soltos | 60 | 273,4 | 2013 a 2025 | sldprt, slddrw, step | CAD | Fora de escopo | Nenhuma ação |

CAD solto fora da pasta Engenharia_CAD, para não entrar em cópia nenhuma:
`Apuama/Templete_Apuama_A4.slddrt`, `Apuama/DT's/*.SLDDRW` (2), `Apuama/VD_antigo/amortecedorVibe/suporte.SLDPRT`.

## C. Telemetria bruta versus repositório dados_telemetria

| Subpasta do Drive | Arquivos | MB | Período | Tipo | Tema | Importância | Destino proposto |
|---|---|---|---|---|---|---|---|
| Telemetria/Motos_2021-2024 | 2633 | 11408 | 2022-11 a 2026-08 | AiM xrk, rrk, drk, gpk | Moto por piloto (20+), inclui superbike | Alta, maior massa de dado próprio, pouco coberta no repo | Amostra por piloto e pista em dados_telemetria; resto fica no Drive |
| Telemetria/SSD_Windows_CLAUDE | 543 | 9696 | 1999 a 2026-08 | mp4, pdf, mat | Resgate de HD: cursos de terceiros, vídeos | Baixa a média | Drive; quarentena para o que duplica Referencias_outras_plataformas |
| Telemetria/F3 | 494 | 623 | 2015 a 2022 | drk, xrk, gpk | AiM F3 (Bortoleto, Barrichello, Aizza), Interlagos e Goiânia | Alta | Amostra em dados_telemetria |
| Telemetria/Referencias_outras_plataformas | 285 | 4375 | 2008 a 2024 | mov, pdf | Cursos e vídeos de terceiros | Baixa | Drive; avaliar duplicata com SSD_Windows_CLAUDE |
| Telemetria/Simuladores | 200 | 222 | 2023 a 2026 | ACC | Dados de simulador ACC | Média | Fixture de simulador na PoC |
| Telemetria/AMG_GT4_26ET06_Interlagos | 147 | 1342 | 2026-07 a 2026-08 | Bosch bmsbin | AMG GT4 por carro | Alta, 100% no repo | dados_telemetria |
| Telemetria/inbox_local_2026-09 | 114 | 99,5 | 2008 a 2026-09 | xlsx, misto | Não triado, 2 arquivos com nome hash | Baixa até triar | Triagem manual |
| Telemetria/AiM_Douglas | 43 | 1343 | 2026-06 a 2026-08 | xrk, zip | Um piloto, zip e pasta extraída do mesmo conteúdo | Média | Amostra em dados_telemetria; quarentena para o zip |
| Telemetria/Motos_2026_12MBR-BSB | 32 | 58,0 | 2026-08-29 | xrk | Moto em Brasília, recente | Alta, não está no repo | dados_telemetria |
| Telemetria/Kart_Guara | 24 | 36,4 | 2022-04 | xrk, rrk | Kart | Alta, única de kart | dados_telemetria |
| Telemetria/MoTeC_Workspaces | 478 | 60,4 | até 2026-08 | i2wkb, mt2, lay | Configuração de workspace MoTeC | Baixa como dado, útil como config | Drive |
| Telemetria/KW | 19 | 0,8 | 2008 a 2013 | ini, txt | Configuração de amortecedor KW | Baixa | Drive |
| Porsche_Cup/2026 | 213 | 41187 | até 2026-09 | MP4 onboard, pds | Etapa 26ET07; 27 GB são 5 vídeos de um carro | Alta para pds, baixa para vídeo | pds em dados_telemetria; MP4 no Drive |
| Porsche_Cup/2023_MPES | 191 | 891 | 2015 a 2023 | car, cha, ld | Base MoTeC completa de etapa 2023 | Alta | dados_telemetria |
| Porsche_Cup/Docs | 84 | 168 | 2014 a 2026-08 | pdf | Manuais, regulamentos, templates PI, procedimento | Alta, permanente | docs do repositório da empresa |
| Porsche_Cup/2025 | 10 | 883 | 2025-11 | misto | Etapa isolada | Média | dados_telemetria |
| Porsche_Cup/2022 | 5 | 22 | 2022-11 | misto | Etapa isolada | Média | dados_telemetria |
| Outras_Categorias/Estudo_outras_series | 186 | 503 | 2008 a 2026-03 | misto | Stock Car, GT7, superbike, estudo e dado misturados | Média | Separar dado real (repo) de estudo (Drive) |

Comparação por nome de arquivo:

| Direção | Resultado |
|---|---|
| Nomes do repositório encontrados no Drive | 703 de 832 nomes únicos (84%) |
| Nomes do repositório ausentes no Drive | 129: fixtures sintéticas ViGrade (.mf4, .xgr, .vdf), amostras anonimizadas (PilotoA a F.pds) e itens de Trabalho/SARU |
| Nomes do Drive ausentes no repositório | 3364: AiM bruto de moto e F3, vídeo onboard, curso de terceiro, instalador |

Cobertura por formato de data logger (nomes únicos no Drive, presentes no repositório):

| Formato | Fabricante | Drive | No repo | Ausente |
|---|---|---|---|---|
| .bmsbin | Bosch | 96 | 96 | 0 |
| .pid | PI Toolbox | 25 | 25 | 0 |
| .vbo | Racelogic | 6 | 6 | 0 |
| .ldx | MoTeC | 42 | 26 | 16 |
| .pds | PI Toolbox | 61 | 36 | 25 |
| .ld | MoTeC | 120 | 35 | 85 |
| .dat | PI Toolbox | 70 | 31 | 39 |
| .gpk | AiM | 340 | 62 | 278 |
| .drk | AiM | 478 | 69 | 409 |
| .rrk | AiM | 510 | 60 | 450 |
| .xrz | AiM | 451 | 50 | 401 |
| .xrk | AiM | 687 | 59 | 628 |
| .xlsx | planilha | 8 | 5 | 3 |
| .csv | planilha | 10 | 1 | 9 |

Bosch, PI `.pid` e Racelogic estão 100% no repositório. AiM (moto e F3, a maior massa) está
em cerca de 15%. MoTeC e PI `.pds` pela metade. Nenhum `.mf4` real de motorsport no Drive;
os do repositório são saída sintética de simulação.

Categoria por pasta: Porsche Cup e AMG GT4 bem cobertas; F3, superbike e moto fracas; kart
presente com pouco volume; ACC sem nome batendo; Stock Car e GT7 misturados em Estudo_outras_series.

Problemas em C:

- `Joao Gonçalves.pds` e `Joao Golçalves.pds` no mesmo outing de 26ET07: mesma sessão, grafia diferente.
- `SCHD0025.MOV` (1,67 GB), `SCHD0075.MOV` e o vídeo de Watkins Glen existem idênticos em nome
  e tamanho em `SSD_Windows_CLAUDE/...` e em `Referencias_outras_plataformas/...`.
- `AiM_Douglas`: dois zips e uma pasta extraída com o mesmo conteúdo.
- `inbox_local_2026-09/f3a8dccdf04579ec.xlsx` e `40f66eccb86d4458.xlsx` sem contexto.
- `Motos_2021-2024` tem um `.slx` com sufixo "(copy)" e um `.html` soltos na raiz.
- No repositório, 97 blobs aparecem sob mais de um caminho (ex.: licença HWA em
  `referencia/RaceCon/License Files/` e `referencia/RaceCon/RaceCon/License Files/`).
- `Porsche_Cup/2026/26ET07/onboards` concentra 27 GB em 5 MP4 de um piloto.

## Segredos

| Caminho | Tamanho | Ação |
|---|---|---|
| Trabalho/SARU/03_Marketing/.env | 74 bytes | Quarentena; rotacionar qualquer chave dentro; conferir `.gitignore` do repositório de marketing |

Único achado por nome em A, B e C. Nenhum `credentials`, `token`, `id_rsa`, `.pem` ou JSON
de service account.

## Listas propostas para a skill quarentena (nada executado)

```
# quarentena-segredos.txt
Trabalho/SARU/03_Marketing/.env
```

```
# quarentena-instaladores.txt
Trabalho/SARU/SaruSys-dados/resgate_lixeira_toshiba/saru-app/data/telemetry/pendrive_amg_gt4/Documentos/RaceCon/RaceCon_2.9.0.7_Setup.exe
Trabalho/SARU/SaruSys-dados/resgate_lixeira_toshiba/saru-app/data/telemetry/pendrive_amg_gt4/Documentos/RaceCon/RaceCon_2.10.1.1_Setup.exe
Trabalho/SARU/SaruSys-dados/resgate_lixeira_toshiba/saru-app/data/telemetry/pendrive_amg_gt4/Documentos/RaceCon/RaceCon_2.11.1.1_Setup.exe
Trabalho/SARU/SaruSys-dados/resgate_lixeira_toshiba/saru-app/data/telemetry/pendrive_amg_gt4/Documentos/RaceCon/RaceCon/RaceCon_2.11.1.1_Setup.exe
Trabalho/SARU/SaruSys-dados/resgate_lixeira_toshiba/saru-app/data/telemetry/pendrive_amg_gt4/Documentos/RaceCon/RaceCon.rar
Trabalho/SARU/SaruSys-dados/resgate_lixeira_toshiba/saru-app/data/telemetry/pendrive_amg_gt4/Documentos/RaceCon/dotNetFx35setup.exe
```

```
# quarentena-duplicatas-a-confirmar.txt (comparar conteúdo antes de mover)
Estudo/Apuama/Historico_SARU_KB/Apuama/VD_antigo.zip
Estudo/Apuama/Historico_SARU_KB/Apuama/Projeto Trainee/sobras_restos/  (114 arquivos)
Trabalho/Telemetria/AiM_Douglas/01_Telemetria_Pastas_Pilotos.zip
Trabalho/Telemetria/AiM_Douglas/Douglas - Telemetria e Dados de Corrida (AiM Sports)-20260831T005037Z-1-001.zip
Trabalho/Telemetria/SSD_Windows_CLAUDE/Motorsport/02_Outras_categorias/Estudo_outras_series/Race3/TrailBrake_Romanowski_LimeRock_July2021/SCHD0025.MOV
```

```
# revisar-nome-hash-e-grafia.txt
Trabalho/Telemetria/inbox_local_2026-09/f3a8dccdf04579ec.xlsx
Trabalho/Telemetria/inbox_local_2026-09/40f66eccb86d4458.xlsx
Trabalho/Porsche_Cup/2026/26ET07/telemetria/antigo/Outing/38#285 - TE1.1 - 23.07 - 15h48m16s - Joao Golçalves.pds
```
