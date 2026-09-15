# saru-plataforma

Repositório de código da SARU: leitores, modelos, pipeline, interfaces, testes e o documento preso
ao código. A empresa (decisão, requisito, física documental, marca, negócio, processo, pesquisa,
auditoria, mocks) mora em `vitormtt/saru`. Português em código, commit e documento.
Foco: Engenheiro primeiro, depois Piloto; as outras famílias vêm a partir delas. Regra de operação e de
escrita mora em `~/.claude/CLAUDE.md`; aqui só o que é deste repositório.

## Onde está cada coisa

| Caminho | O que é |
|---|---|
| `src/saru_poc/` | código da família Piloto, herdado da PoC; leitores em `readers/` |
| `web/` | frontend Vite; `make web` na 5177, API em `make api` na 8010 |
| `migrations/` | SQL do PostgreSQL, uma por número; `make migrate` aplica |
| `docs/decisions.md` | decisão de produto (regra de leitor, issue, medição), uma linha por decisão; só cresce |
| `docs/requisitos/` | requisitos da família Piloto, até o `saru` PR 20 mesclar; depois saem daqui |
| `docs/arquitetura/adr/` | sete ADRs da PoC; ADR único citando decisão e requisito |
| `docs/*-medicao.md` | tabela de medição de cada leitor (E-RN-02) |
| `docs/html/<issue>.html` | antes e depois de cada issue, atualizado no lugar |
| `docs/handoff/caixa-*.md` | conversa com o Antigravity: M<n> em `caixa-antigravity.md`, R<n> em `caixa-claude.md` |

## Regras do repositório

1. `main` só muda por PR; nenhum agente mescla; nada entra sem Vitor ter lido. Um PR por vez.
2. Número de física só com tabela de medição no acervo (E-RN-02). Estimativa é rascunho.
3. Issue fecha só com o protocolo de `vitormtt/saru` `docs/processo/validacao-de-issue.md`: roteiro de
   conferência de 3 a 5 passos, antes e depois em `docs/html/<issue>.html` e tabela de medição.
4. Ordem das issues (portadas da PoC): #25 e #26, depois #27 e #28, depois #29, #30, #31, #32, #33.
5. Nada em `src/` sem issue. Branch `<fam>/<issue>-<tema>` (pil, equ, eng, cam, alu, emp).
6. Decisão de produto vai para `docs/decisions.md` na mesma sessão; decisão de empresa vai para
   `vitormtt/saru` `docs/decisions.md`.
7. Antigravity pesquisa, varre e mede; Claude escreve código e documento. Resposta R<n> não é
   aprovação de Vitor.
8. Acervo de telemetria fica no Drive (`~/gdrive/Trabalho/`); nunca versionar gravação.

## Comandos

`make setup`, `make up`, `make migrate`, `make test`, `make doctor`. Banco só PostgreSQL.
`make up` antes de `make test`: teste pulado por falta de banco reprova a suíte e não conta como verde.
