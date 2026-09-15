# Simulador transiente 14-DOF (Julia)

Serve a PIL-RF-30 e E-RF-09. Arquitetura em
`docs/arquitetura/adr/ADR-008-engenharia-reversa-e-simulacao-de-volta.md`.

Motor de maior fidelidade da simulação de volta, fora do pacote Python de propósito
(ADR-008): consome os parâmetros que `src/saru_poc/fisica/calibracao_reversa.py` calibra,
por um arquivo de troca só, nunca por import direto Python↔Julia.

## Estado

Vazio. Preparado em 2026-09-15 pela issue #49, ainda sem código. O operador já validou o
modelo 14-DOF em Julia noutro projeto (PIBIC, `~/Desktop/PIBIC/14DOF`); a adaptação para o
GT3 Cup e para o formato de troca desta plataforma é o próximo passo, não feito aqui.

## Arquivo de troca (rascunho, a fechar em `docs/modelos/`)

JSON com os `ParameterValue` calibrados (valor, unidade, proveniência, fonte) e a série de
entrada (tempo, curvatura, referência de velocidade). Schema formal ainda não escrito; ver
issue #49 antes de gerar ou consumir qualquer arquivo desse formato.
