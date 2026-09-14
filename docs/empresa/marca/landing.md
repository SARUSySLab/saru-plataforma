---
titulo: "Landing e Narrativa"
data: "2026-07-15"
origem: "_arquivo/saru-docs/docs/produto/landing.md"
status: "vigente"
area: "marca"
---

# Landing e Narrativa

Regra-mestra (GTM 2026-07-15): **o pitch so afirma o que o codigo sustenta
hoje.** Roadmap se vende como roadmap. Ninguem compra DOF, compra decimos de
segundo e dinheiro economizado; a matematica entra como prova, nunca como
manchete.

## Hero

Transforme telemetria real em decisao de pista com referencia simulada.

## CTAs

- Agendar demo tecnica.
- Entrar no early access.

## Claims permitidos

- Plataforma de analise e simulacao correlacionada para motorsport.
- MVP focado em telemetria, comparacao de voltas e referencia simulada.
- Solver rapido separado de camada beta de alta fidelidade.
- Rastreabilidade por canal, fonte, solver e versao.

## Claims bloqueados

- 14-DOF validado comercialmente.
- IA recomenda setup automaticamente.
- Substitui MoTeC, ATLAS ou Race Studio.
- Prediz tempo real com precisao final.

## Guardrails de honestidade (pode vs nao pode)

| Pode afirmar | Nao pode afirmar | Por que |
|---|---|---|
| "Solver de lap-time validado contra referencia (+/- 1 s em Interlagos)" | "Simulador 14-DOF operacional" | 14-DOF e fase 2 de engenharia; hoje e QSS |
| "Fisica validada contra benchmark publicado" | "Precisao de gemeo digital" | Validacao e pontual (roll gradient), nao global |
| "Plataforma de telemetria funcional e testada" | "Produto completo em producao com clientes" | Simulacao via UI ainda tem trecho mock; zero cliente pagante |
| "Parcerias ativas" | Nomes de clientes/resultados nao autorizados | Parceria nao e contrato fechado ate assinar |
| "Roadmap para fidelidade de fabrica (14-DOF, pneu termico)" | Datas duras de entrega | Dev solo; risco de execucao real |

Investidor tecnico faz due diligence: uma inconsistencia entre pitch e repo
mata a credibilidade das demais claims. Honestidade sobre o estagio e sinal de
maturidade, usar a favor.

## Traducao tecnica -> comercial (resumo)

| Ativo tecnico real | Frase permitida | Prova |
|---|---|---|
| QSS validado vs oraculo (992 GT3 R @ Interlagos, 94 s +/- 1 s) | "Testamos centenas de configuracoes do seu carro antes de voce gastar um jogo de pneus." | Baseline de regressao GREEN 93,03 s |
| Telemetria assincrona 1000 Hz testada | "Cada sensor do carro, ao vivo, na tela do engenheiro, no box ou remoto." | Engine com testes |
| 3-DOF validado vs Khalil 2018 | "Nossa fisica e validada contra pesquisa publicada." | Teste de roll gradient + `validation/` |
| Arquitetura web/cloud multi-servico | "Concorrentes vendem software de 2005 preso num PC. Nos vendemos uma sala de engenharia na nuvem." | Demo ao vivo do hub |
| 14-DOF acausal Julia, ROADMAP | "Estamos construindo o motor de proxima geracao." | Somente como visao |

Matriz completa, elevator pitches e material de aquisicao: KB `50_company/`
(interno, nao publicar).
