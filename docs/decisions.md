# Decisões

Uma linha por decisão: data, decisão, motivo, alternativa descartada, status.
Origem: plano consolidado da auditoria de 2026-09-12 (`_auditoria/00-plano-consolidado.md`
na pasta guarda-chuva) e o chat com Vitor.

| Data | Decisão | Motivo | Alternativa descartada | Status |
|---|---|---|---|---|
| 2026-07-15 | O pitch só afirma o que o código sustenta | Honestidade de claim | Vender roadmap como produto | aprovada |
| 2026-09-12 | Processo git da organização é GitHub Flow: `main` protegida, branch por tarefa, merge só por PR aceito | Time pequeno, PR como revisão | Git Flow com `develop` | aprovada |
| 2026-09-12 | Time: Vitor e Lucas Antunes; `ciro-c` removido; Vinicius saiu | Admin pode apagar repositório | Manter membros sem papel | aprovada |
| 2026-09-12 | `saru-poc-trackday` é o repositório da família Piloto; `saru-app` e demais ficam arquivados como fonte de peças | Um histórico só; Lucas não perde nada | Terceiro repositório de produto | aprovada |
| 2026-09-12 | Sprint de uma semana; issue no modelo de requisito com prefixo; milestone por marco; um Projects por repositório | Modelo da disciplina de requisitos | Issues livres | aprovada |
| 2026-09-12 | Cinco famílias por nicho: Piloto, Campeonato, Engenheiro, Equipe, Aluno; Hase é parceiro; hardware só após DashAuto | Segmentar é mais fácil de fazer e vender | Um produto para todos | aprovada |
| 2026-09-12 | Ordem das famílias: Piloto, Campeonato, Engenheiro, Equipe, Aluno | O que existe, receita da consultoria, presencial como prioridade | Engenheiro primeiro | aprovada |
| 2026-09-12 | Uma semana de documentação e modelagem antes de codar qualquer família; poucos ADR | Duas gerações nasceram sem requisitos | Codar e documentar depois | aprovada |
| 2026-09-12 | Português em código, commit e documentação nos repositórios da SARU | Time, cliente e acervo brasileiros; PoC já em português | Inglês, como nos arquivados | aprovada |
| 2026-09-12 | Do acervo Apuama, absorver dinâmica veicular e pneu; CAD nunca | Conteúdo técnico útil | Copiar tudo | aprovada |
| 2026-09-13 | Repositório da empresa `saru` nasce no usuário `vitormtt`, privado, com `main` protegida; a PoC fica na organização | Proteção de branch é gratuita no pessoal (Pro de estudante) e paga na organização | Team pago; repositório público | aprovada |
| 2026-09-13 | E-RF-09: estimar parâmetros do carro a partir do dado e simular volta com modelo de piloto | Nunca tinha sido escrito; existe em pedaços | | aprovada |
| 2026-09-13 | Carro de referência da física: Porsche 911 GT3 Cup 991.1, 991.2 e 992.1 | Acervo real da Porsche Cup Brasil | 992 GT3 R (calibração antiga) | aprovada |
| pendente | Estratégia de merge: squash com histórico linear | Um commit por PR | Merge commit | recomendada |
| pendente | Documentação por repositório, sem portal MkDocs | Portal morreu em julho | Reviver `saru-docs` | recomendada |
| pendente | `SPM.md` acaba; estado vivo vira issue | Ninguém lia | Manter | recomendada |
| pendente | ADR mestre único em `saru/docs/adr/` | Hoje em 4 lugares | | recomendada |
| pendente | Física em `saru/docs/fisica/` até existir repositório de física | Sem código, sem repositório | | recomendada |
| pendente | Drive: `Trabalho/SARU` em 4 áreas; quarentena de `.env`, instaladores e logs; Apuama VD e pneu para `docs/fisica/` | Auditoria 05 | | recomendada |
