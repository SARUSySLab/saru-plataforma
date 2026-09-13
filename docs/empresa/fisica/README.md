# Física

Modelos, parâmetros e calibrações com fonte e status de validação. Esta pasta guarda
documento, não código: o repositório `saru` registra decisão, requisito e processo, e o
produto vive no repositório da família.

Os parâmetros do Porsche 911 GT3 Cup, nas gerações 991.1, 991.2 e 992.1, vivem na PoC em
`saru-poc-trackday`, no pacote `src/saru_poc/fisica/`. A conferência de cada valor contra a
fonte que ele cita está em `docs/fisica-parametros-gt3-cup.md`, no mesmo repositório.

## Subpastas

| Pasta | O que guarda |
|---|---|
| `modelos/` | arquitetura de simulação, escopo de veículos, pacote de validação |
| `dinamica/` | dinâmica veicular, transferência de carga, freio, aerodinâmica, 14 graus de liberdade |
| `pneus/` | Pacejka, sensibilidade à carga, física de pneu |
| `calibracao/` | formatos de pista e material de calibração |
