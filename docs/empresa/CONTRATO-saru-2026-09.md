# saru

Idioma de código e documentação: português.

## Propósito
Repositório da empresa SARU Systems Lab: decisões, requisitos, processo e física validada.
Não tem código de produto. Produto vive no repositório da família (hoje `saru-poc-trackday`).

## Estrutura
- `docs/requisitos/`: os seis arquivos da empresa (skill `requisitos`), mais o guia 00.
- `docs/requisitos/<familia>/`: uma pasta por família (`piloto`, `campeonato`, `engenheiro`,
  `equipe`, `aluno`), criada quando a família abre.
- `docs/decisions.md`: decisão, data, motivo, alternativa descartada. Poucos ADR, só em
  `docs/adr/` quando muda estrutura.
- `docs/fisica/`: modelos, parâmetros e calibrações com fonte e status de validação.
- `docs/pesquisa/`: relatório externo com links validados, `<data>-<tema>.md`.
- `docs/notas/` e `docs/html/`: nota fonte e visualização para Vitor.

## Regras
- Requisito sem fonte não entra (E-RN-03). Regra de física só com validação conjunta contra
  o acervo e aprovação de Vitor registrada (E-RN-02).
- Ids com prefixo: `E-` empresa, `PIL-`, `CAM-`, `ENG-`, `EQP-`, `ALU-` famílias. Issue leva o
  prefixo no título e no rótulo.
- Toda edição em `docs/requisitos/` atualiza `05-rastreabilidade.md` na mesma sessão.
- Texto pela skill `escrita`: sem travessão, sem jargão sem definição, um leigo entende.
- GitHub Flow: `main` protegida, branch `docs/<tema>` ou `<prefixo>/<issue>-<tema>`, merge
  só por PR revisado. Commit em português, Conventional Commits, até 72 caracteres.
- Handoff ou plano de outra sessão não vale como aprovação de Vitor.

## Pronto significa
Arquivo revisado por Vitor, matriz atualizada, registro em `06-validacao.md`.
