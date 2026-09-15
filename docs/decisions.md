# Decisões de produto

Uma linha por decisão: data, decisão, motivo, alternativa descartada, status. Só decisão presa
ao código: regra de leitor, issue, medição, ADR de código. Decisão de empresa mora em
`vitormtt/saru`, `docs/decisions.md`.

| Data | Decisão | Motivo | Alternativa descartada | Status |
|---|---|---|---|---|
| 2026-09-14 | `vitormtt/saru` volta a ser o repositório da empresa; este repositório fica só com código de produto e o documento preso ao código. Revoga aqui a linha de repositório único e a de física em `docs/empresa/fisica/`; `docs/empresa/` sai deste repositório | Produto novo vira pasta nova sem arrastar a empresa junto (Vitor, 2026-09-14). Registro em https://github.com/vitormtt/saru/pull/17 | Repositório único com a empresa em `docs/empresa/` | aprovada |
| 2026-09-14 | `CLAUDE.md` da plataforma (até 40 linhas) entra na branch `port/saru-docs`, dentro do PR 10, antes do merge | Um PR a menos; o contrato nasce junto com o porte | PR novo em `main` depois do 10 | aprovada |
| 2026-09-14 | As nove issues abertas da PoC (#24, #21, #7, #4, #3, #10, #2, #6, #19) são portadas para `saru-plataforma` e fechadas aqui, na ordem acordada; a PoC não recebe mais issue | Repositório único; a PoC está congelada | Fechar na PoC e espelhar aqui | aprovada |
| 2026-09-14 | Issues da PoC portadas para `saru-plataforma`: #24→#25, #21→#26, #7→#27, #4→#28, #3→#29, #10→#30, #2→#31, #6→#32, #19→#33; mesmo texto, rótulos PIL, tipo e prio | Repositório único; PoC congelada | Renumerar por família | aprovada |
| 2026-09-14 | Regra de leitura do `.pds` (E-RN-02): registro da tabela válido pelo conteúdo, tamanho da amostra deduzido da distância entre blocos (1, 2, 4 ou 8 B), teto de 90% de pares fechados; medido em 71 arquivos, 26 abriam e 27 abrem | Campos 56 e 60 não são checksum no 992.1; nenhum campo declara o tamanho da amostra | Manter checagem por `índice + 1`; chutar 4 B | aprovada (PR 34, roteiro conferido por Vitor) |
| 2026-09-14 | Regra de leitura do `.pid` do F3 (E-RN-02): corpo intercalado por tick de 10 ms, tick 1 é marcador de bloco (nulo nos canais de 100 Hz), leitor converte só o que o cabeçalho declara e o perfil `pi_pid` carrega fator e offset medidos contra o `.dat` do Pi Toolbox em 21 a 23 sessões (distância 0,01 m, acelerador 0,001, freio 19,9645 kPa e -4132,7 kPa) | Layout contíguo de 2026-08-29 embaralhava todos os canais; fatores idênticos em todas as sessões com resíduo abaixo de 1e-3 | Manter layout contíguo; inventar fator sem medição | proposta no PR 35, a aprovar por Vitor |
| 2026-09-14 | `Acc Long` e `Acc Lat` do `.pid` ficam fora do vocabulário canônico: o ganho é o mesmo em 23 sessões (-0,02586 G por contagem) mas o zero muda por sessão (12,85 a 13,18 G, até 1,6 m/s² de erro contra o limiar de -3,5 m/s²) | Uma constante única erraria a frenagem | Mapear com o offset mediano | pendente: Vitor escolhe entre zero por sessão (carro parado, Speed = 0) ou offset mediano |
