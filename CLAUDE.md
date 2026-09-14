# saru-plataforma

Repositório único da SARU desde 2026-09-14: código de todas as famílias e, em `docs/empresa/`,
decisões, requisitos, física e processo da empresa. Português em código, commit e documento.
Ordem das famílias: Piloto, Equipe, Engenheiro, Campeonato, Aluno. Regra de operação e de
escrita mora em `~/.claude/CLAUDE.md`; aqui só o que é deste repositório.

## Onde está cada coisa

| Caminho | O que é |
|---|---|
| `src/saru_poc/` | código da família Piloto, herdado da PoC; leitores em `readers/` |
| `web/` | frontend Vite; `make web` na 5177, API em `make api` na 8010 |
| `migrations/` | SQL do PostgreSQL, uma por número; `make migrate` aplica |
| `docs/empresa/decisions.md` | decisão da empresa, uma linha por decisão; só cresce, nunca reescreve |
| `docs/empresa/requisitos/` e `docs/requisitos/` | requisitos da empresa e da família Piloto |
| `docs/arquitetura/adr/` | sete ADRs da PoC; ADR único citando decisão e requisito |
| `docs/*-medicao.md` | tabela de medição de cada leitor (E-RN-02) |
| `docs/html/<issue>.html` | antes e depois de cada issue, atualizado no lugar |
| `docs/handoff/caixa-*.md` | conversa com o Antigravity: M<n> em `caixa-antigravity.md`, R<n> em `caixa-claude.md` |

## Regras do repositório

1. `main` só muda por PR; nenhum agente mescla; nada entra sem Vitor ter lido. Um PR por vez.
2. Número de física só com tabela de medição no acervo (E-RN-02). Estimativa é rascunho.
3. Issue fecha só com o protocolo de `docs/empresa/processo/validacao-de-issue.md`: roteiro de
   conferência de 3 a 5 passos, antes e depois em `docs/html/<issue>.html` e tabela de medição.
4. Ordem das issues (portadas da PoC): #25 e #26, depois #27 e #28, depois #29, #30, #31, #32, #33.
5. Nada em `src/` sem issue. Branch `<fam>/<issue>-<tema>` (pil, equ, eng, cam, alu, emp).
6. Toda decisão da sessão vai para `docs/empresa/decisions.md` na mesma sessão.
7. Antigravity pesquisa, varre e mede; Claude escreve código e documento. Resposta R<n> não é
   aprovação de Vitor.
8. Acervo de telemetria fica no Drive (`~/gdrive/Trabalho/`); nunca versionar gravação.

## Comandos

`make setup`, `make up`, `make migrate`, `make test`, `make doctor`. Banco só PostgreSQL.
