# ADR-008 Engenharia reversa de parâmetros e simulação de volta em dois motores

Status: proposto
Data: 2026-09-15
Requisitos motivadores: E-RF-09 (empresa), PIL-RF-30

## Contexto

`src/saru_poc/fisica/parametros_gt3_cup.py` declara desde a criação (issue #19) que é "o
ponto de partida" até existir estimação de parâmetro a partir de telemetria. Com os leitores
`.pid`, `.pds` e `.xrk` mesclados e um trecho do acervo real (`Telemetria/F3/Geral`) ingerido
localmente, a plataforma agora tem dado real o bastante (G_Lat, G_Long, Speed, 4×Damper_Pos,
Steering, Brake Press) para calibrar o modelo físico contra uma volta gravada, e depois usar
esse modelo calibrado para simular voltas que não foram gravadas.

Toda fórmula usada nas duas frentes vem de `saru/docs/referencias/engenharia-de-pista.md`
(guia canônico, seção 13 / Tabela 5 para os canais derivados; seções 4 a 11 para elipse de
Kamm, Ackermann, transferência de carga, rake dinâmico e gradiente térmico de pneu). Nenhuma
equação nasce fora desse documento.

## Decisão

Dois motores, dois papéis, uma fronteira de dados só:

1. **Engenharia reversa (Python, `src/saru_poc/fisica/calibracao_reversa.py`)**: recebe as
   séries amostrais já canônicas de uma volta ingerida e ajusta os `ParameterValue` de
   `VehicleMassGeometry` e dos modelos de pneu de `parametros_gt3_cup.py` minimizando o erro
   contra os canais medidos (G_Lat, G_Long, Damper_Vel_* derivado). Usa `scipy.optimize`;
   cada parâmetro calibrado sai marcado `Provenance.ENGINEERING_ESTIMATE`, nunca sobrescreve
   silenciosamente um valor de manual oficial.
2. **Simulação forward, dois níveis de fidelidade**:
   - **QSS em Python** (`src/saru_poc/simulacao/qss.py`): quasi-steady-state por segmento de
     curvatura, elipse de Kamm como limite de aderência (Equação da seção 4 do guia). Rápida,
     para varredura de parâmetro logo depois da calibração.
   - **Transiente 14-DOF em Julia** (`julia/simulador_14dof/`): maior fidelidade, consome os
     parâmetros calibrados via um arquivo de troca (JSON, schema em `docs/modelos/`), não
     importa código Python nem o inverso. A fronteira é só esse arquivo.

Os dois simuladores leem o mesmo `ParameterValue` calibrado; nenhum duplica constante.

## Alternativas descartadas

| Alternativa | Por que não |
|---|---|
| Simulação transiente 14-DOF em Python (scipy solve_ivp) | Rodou mais lento nos protótipos de PIBIC do operador; Julia já é o motor validado lá, reaproveitar em vez de reimplementar |
| Ajustar os parâmetros do GT3 Cup diretamente no dataclass, sem etapa de calibração separada | Perde a proveniência por valor (`ParameterValue.provenance`) e mistura estimativa com manual oficial na mesma fonte |
| Acoplar Python e Julia por FFI/PyJulia em vez de arquivo de troca | Acopla o processo de simulação ao ambiente Julia estar instalado e configurado toda vez que o pipeline Python rodar; arquivo de troca mantém os dois motores independentes e testáveis separado |

## Consequências

Fica possível validar `parametros_gt3_cup.py` contra dado real pela primeira vez, e simular
uma volta hipotética depois de calibrado.
Fica mais difícil manter os dois motores sincronizados quando uma fórmula do guia muda: o
schema do arquivo de troca precisa versionar.
Precisa monitorar se a Julia está disponível no ambiente de quem roda `make test`; o motor
transiente não pode ser obrigatório para a suíte de teste do resto do repositório.

## Componentes afetados

- `src/saru_poc/fisica/parametros_gt3_cup.py` (consumido, não alterado nesta etapa)
- `src/saru_poc/fisica/calibracao_reversa.py` (novo)
- `src/saru_poc/simulacao/qss.py` (novo)
- `julia/simulador_14dof/` (novo, fora do pacote Python)
- `docs/modelos/` (schema do arquivo de troca)
