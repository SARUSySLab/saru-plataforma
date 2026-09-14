---
titulo: "SARU - Dossiê de Decisões (research embasado)"
data: "2026-08-19"
origem: "_arquivo/saru-app/docs/plans/mvp-decisoes-research.md"
status: "obsoleto"
area: "processo"
---

# SARU - Dossiê de Decisões (research embasado)

Versão: 1.0
Data: 2026-07-10
Escopo: embasar com fontes web primárias as 6 decisões pendentes do §5 do seguimento (`mvp-higiene-arquitetura-seguimento.md`), para escolha do dono antes de prosseguir. Cada decisão traz **evidência citada**, **prática de mercado/norma**, **recomendação** e **nível de confiança**.

> Método: deep-research (fan-out web + fetch) + verificação direta das fontes primárias em 2026-07-10. As afirmações abaixo foram conferidas na fonte oficial citada (OWASP, git-scm, GitHub Docs, rclone, OptimumG, ISO/SAE), não apenas em resumo de agente. Estado de código reconferido no repo em 2026-07-06/07.

---

## Nota de contexto, o que mudou desde o seguimento v0.2

A verificação de 06-07/07 encontrou parte do backlog **já executada** por sessões anteriores, o que reformula 4 das 6 decisões:

- **Segurança:** CORS wildcard, secrets hardcoded e porta do engine em prod **já corrigidos** (`main.py:38-49` allowlist por env; compose usa `${VAR:?required}` sem literal; prod só publica `nginx :80`). Resta o item **estrutural** (rotas do engine sem auth atrás do catch-all + jobs async sem guard).
- **Banda 14-DOF:** a banda larga 96-112s **já foi substituída** por completude determinística (`lap<140`, sem DNF) + invariantes físicos (`e_y≤1.8m`, utilização≤1.05, slips) + `@test_broken abs(lap−94)≤1` como alvo NMPC (`test/runtests.jl:187-194`). Lap limpo atual ~100.7s.
- **CI core-jl:** **verde e reproduzível**, `reference/vehicle_992_gt3_r.yaml` + `interlagos.hdf5` foram tirados do `.gitignore` e commitados (`890a2a2`); últimas 3 runs `develop` = success.
- **`src/ai/` stubs:** **removidos** do develop no mesmo commit (`890a2a2`); o scaffold grande sobrevive só no branch local `feature/claude-phase3-scaffold` (`baf4536`, ~2.3k linhas em 4 módulos, sobre um develop antigo).
- **SARU PR #1 (KB):** **fechado sem merge** por Vitor em 05/07; branch apagado no remoto. No comentário de fechamento ele diz que **não tem mais a licença VI-CRT**, reformula o bloqueante do segredo (§ Decisão 5).
- **T03 espelhado no Python:** oráculos do `saru-core` rebaselineados para bandas interinas **86.18s / 99.36s** (alvo real 94.0-94.4 / 103.5-105.0 mantido no doc).

---

# Decisão 1, Batch/DOE de setup no MVP

**Pergunta:** ligar a UI ao endpoint real de sweep (síncrono, cap 64 combos, QSS) ou ocultar a feature? Complicador: só 3 parâmetros são vivos no QSS (`wing_position`, `tyre_pressure_bar`, `brake_bias_offset`, `lapsim_service.py:113`), enquanto a UI hoje varre `fuel/pressure/wing/camber/ride` (`LtsSimulatorView.tsx:32`), sendo o batch atual **sintético** ("FAKE grid solver… synthetic penalty model", L147).

**Evidência (o que o mercado faz):**
- **OptimumG / OptimumLap**, declara explicitamente na página do produto: *"The vehicle model used in OptimumLap is a point mass, quasi-steady state model… no weight transfer or transient effects are taken into account"*, e expõe para estudo **exatamente os parâmetros que o modelo responde**, "engine power, gearbox characteristics, aerodynamics, tires and suspension, and mass", **sem camber/ride-height** como eixos de sweep. Vende honestidade da simplicidade: *"estimate lap times with up to 10% accuracy"* dito na cara. [optimumg.com/product/optimumlap](https://optimumg.com/product/optimumlap/)
- **Canopy Simulations** (referência de mercado, F1/motorsport), o sweep é amarrado ao **parâmetro que o modelo de fato contém**: o usuário varre um path do car model (ex. `car.chassis.mCar`); o tutorial de onboarding roda um **sweep real de 20 pontos** (não canned), com o solver Quasi-Static Lap. E documenta o **envelope de validade**: quando a mudança viola uma restrição integral, a sensibilidade de lap-time agregada "is stated to be wrong". [blog.canopysimulations.com/getting-started-1](https://blog.canopysimulations.com/getting-started-1-sign-in-run-a-study-1ba36089abbd)
- **VI-grade / VI-CarRealTime**, DOE/Design Exploration é feature de primeira classe ("Five Reasons Customers Choose"), e a **razão #1 é validação**: resultados confiáveis porque o modelo é correlacionado com teste físico. [vi-grade.com/…/vi-carrealtime](https://www.vi-grade.com/en/products/vi-carrealtime/)

**Leitura:** o padrão de mercado é **expor só os eixos que a física resolve, e ser explícito sobre o resto**. O SARU já tem essa honestidade no backend, o endpoint responde **422 para parâmetro inerte** (`lts.py:258`). O que quebra a regra é a UI sintética, que é o oposto do que a Canopy faz no primeiro clique.

**Recomendação:** **Ligar a UI ao `/api/lts/run-batch` real, mas com o escopo de eixos reduzido aos 3 vivos** (wing, pressure, brake-bias) e um rótulo honesto do tipo "QSS fast sweep, corner-level (camber/ride) chega no tier 14-DOF". Ocultar é a segunda melhor opção; manter o fake é o único inaceitável (é o "fake com cara de real" que a matriz de confiança proíbe). **Confiança: alta.**

---

# Decisão 2, Segurança mínima antes de beta fechado

**Pergunta:** o item estrutural que resta (rotas do engine FastAPI sem auth atrás do catch-all `/api/*` do proxy, upload, análise, CRUD de veículos/setups, + `SimulationJobsController` async/SSE sem guard) é **must-fix antes do primeiro beta** ou hardening pós-beta?

**Evidência (OWASP API Security Top 10 2023, oficial):**
- **API2:2023 Broken Authentication**, *"a microservice is vulnerable if: Other microservices can access it without authentication."* Perfil de risco: **exploitability Easy · prevalence Common · detectability Easy · technical impact Severe.** Consequência declarada: *full account takeover and unauthorized sensitive actions.* [owasp.org/API-Security/…/broken-authentication](https://owasp.org/API-Security/editions/2023/en/0xa2-broken-authentication/)
- **API8:2023 Security Misconfiguration**, vulnerável se hardening falta em **qualquer camada da stack** → um engine FastAPI "interno" exposto via proxy catch-all **está no escopo da norma, independentemente de ser interno**. Mesmo perfil Severe. [owasp.org/API-Security/…/security-misconfiguration](https://owasp.org/API-Security/editions/2023/en/0xa8-security-misconfiguration/)
- **OWASP File Upload Cheat Sheet**, controle de baseline nomeado: *"Only allow authorized users to upload files"*; e *"The Content-Type for uploaded files is provided by the user, and as such cannot be trusted"* → um proxy pass-through **não fornece segurança de upload**; a validação tem de ser no serviço. [cheatsheetseries.owasp.org/…/File_Upload_Cheat_Sheet](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)

**Leitura:** endpoint de upload sem auth é o cenário exato que a OWASP marca como Severe + fácil de explorar (inclusive DoS por encher storage). "É interno, está atrás do proxy" **não isenta** pela própria letra da norma. Baseline OWASP-aligned e pragmático para beta: **service-key no hop BFF→engine** (API key é permitida para auth máquina-a-máquina) **+ auth de usuário real nas rotas que mutam dado** (upload, CRUD, controle de job).

**Recomendação:** **Must-fix antes do beta fechado**, mas é barato: rotear o CRUD restante pelo BFF guarded (padrão já usado em CRM/ERP/vehicles, ADR-0009), pôr `@UseGuards(JwtAuthGuard)` no controller async, e um segredo compartilhado no hop interno. Não precisa ser a Fase D inteira (migrations versionadas podem ficar para depois). **Confiança: alta.**

---

# Decisão 3, Banda de regressão do simulador físico em CI

**Pergunta:** além de completude + invariantes físicos, adicionar uma banda estreita de regressão em torno do lap determinístico atual (~100.7s ± 1-2s)? Ou manter só completude + invariantes?

**Evidência:**
- **Validação por canal > lap-time-only.** OptimumLap descreve validação **per-channel** (apex speeds, end-of-straight speeds, energy consumption, e lap time), não só lap. VI-grade ancora confiança na **correlação com teste físico**, não no número de lap. (fontes da Decisão 1.)
- **Tolerância de referência de mercado:** OptimumLap declara **~10% de acurácia** de lap-time vs dado real para um QSS ponta-a-ponta, ou seja, lap-time é métrica *grossa*; travar CI num lap com tolerância fina não mede fidelidade física.
- **TUM QSS** (Heilmeier et al., *A Quasi-Steady-State Lap Time Simulation for Electrified Race Cars*), QSS entrega "accurate results within a short computing time and easy parametrization"; a referência acadêmica valida por **estrutura física + canais**, não por golden-lap em CI. [portal.fis.tum.de/…/quasi-steady-state-lap-time](https://portal.fis.tum.de/en/publications/a-quasi-steady-state-lap-time-simulation-for-electrified-race-car) · [github.com/TUMFTM/laptime-simulation](https://github.com/TUMFTM/laptime-simulation)

**Leitura:** o desenho atual (completude determinística + invariantes físicos `e_y`/utilização/slips + `@test_broken` marcando o alvo 94±1) **já está alinhado com a boa prática de V&V**, testa a física, não o número. Adicionar um golden-lap estreito num modelo que ainda vai recalibrar (load sensitivity, aero real, pneu real pendentes) só produziria **falsos vermelhos** a cada melhoria física legítima. A regressão *fina* faz sentido no **QSS já calibrado** (onde ela existe: `QSS_REFERENCE_S` ±1.0), não no 14-DOF em evolução.

**Recomendação:** **Manter completude + invariantes; NÃO adicionar golden-lap estreito no 14-DOF** enquanto a recalibração física estiver aberta. Opcional de baixo custo: um **guard largo anti-explosão** (ex. `90 ≤ lap ≤ 115`) só para pegar regressão catastrófica, sem fingir precisão. Quando o 2.4 (channel validation) fechar, aí sim uma banda + correlação por canal. **Confiança: alta.**

---

# Decisão 4, Scaffold NMPC grande parado vs incremental

**Pergunta:** manter o branch local `feature/claude-phase3-scaffold` (~2.3k linhas, 4 módulos NMPC não exercitados, sobre develop antigo) como base da Fase 3, ou descartar e reconstruir incremental quando a fase começar?

**Evidência:**
- **Referências open-source de NMPC de corrida são compactas e focadas.** O **ETH/AMZ MPCC** (alexliniger/MPCC, 1.8k stars) é uma *focused reference implementation*: bicycle model + magic formula, formulação MPC (progress vs contouring/lag error), sistema de constraints, e solver (QP time-varying via hpipm). Não é um mega-scaffold, é núcleo enxuto. [github.com/alexliniger/MPCC](https://github.com/alexliniger/MPCC)
- **AMZ fssim / TUM** seguem o mesmo padrão de módulos pequenos e testáveis. [github.com/AMZ-Driverless/fssim](https://github.com/AMZ-Driverless/fssim)
- **Custo de branch parado (engenharia de software):** pesquisa DORA/State of DevOps associa **vida de branch < 1 dia e < 3 branches ativos** a maior performance de entrega; um branch de ~2.3k linhas não-mergeado, sobre base antiga, é dívida de merge crescente + bit-rot. YAGNI e "big design up front" penalizam scaffold não-exercitado.
- **Risco específico do SARU (já registrado):** a memória de fase-3 diz que o GP/tube **depende do 2.4 (channel validation)**, treinar sobre o resíduo 3↔14-DOF agora aprenderia o fudge, não a física. O scaffold foi escrito **antes** disso e sobre uma base que já divergiu (o próprio `Transient14DOF.jl` mudou 244 linhas desde então).

**Leitura:** o scaffold tem valor como **referência de design** (os F1-F10 do verifier, a estrutura de 4 módulos), mas mantê-lo vivo como branch destinado a merge é dívida que só cresce, e ele terá de ser re-derivado sobre o 14-DOF atual de qualquer jeito. O padrão de mercado é núcleo enxuto construído incremental.

**Recomendação:** **Não manter como branch de merge.** Extrair o design para um **doc** (`docs/STAGE3-NMPC-DRIVER-PLAN.md` já existe, enriquecer com os F1-F10 e as assinaturas dos 4 módulos), arquivar o branch com uma tag (`archive/phase3-scaffold-baf4536`) para não perder o código, e **reconstruir incremental** quando o Passo 0 da Fase 3 começar (expor inputs do 14-DOF + portar 3-DOF Frenet + fechar 2.4). **Confiança: média-alta** (média só porque depende de quanto do scaffold é reaproveitável, vale um diff de 1h antes de arquivar).

---

# Decisão 5, Remediação de segredo commitado + padronizações

**Contexto atualizado:** o endpoint de licença foi commitado num branch de PR **fechado sem merge e apagado no remoto**; Vitor declarou que **não tem mais a licença**. Isso rebaixa a urgência do segredo (credencial provavelmente morta), mas a guidance ainda vale porque o commit **pode continuar acessível**.

**Evidência (GitHub Docs, "Removing sensitive data from a repository", oficial):**
- **1º passo quando é segredo:** *"if the sensitive data you need to remove is a secret (password/token/credential)… as a first step you need to revoke and/or rotate that secret."* Rotação sozinha pode tornar a reescrita de histórico desnecessária. [docs.github.com/…/removing-sensitive-data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
- **Ferramenta:** GitHub hoje recomenda **`git-filter-repo`** (flag `--sensitive-data-removal`, v2.47+). **BFG Repo-Cleaner não é mais mencionado** na página atual.
- **Force-push não basta:** *"the commits with sensitive data may still be accessible… In any clones or forks… Directly via their SHA-1 hashes in cached views on GitHub… Through any pull requests that reference them."* → para caches/PR fechados, abrir ticket no **GitHub Support**.

**Padronizações que continuam válidas (para quando a KB voltar em PRs menores):**
- **rclone filtros, first-match-wins (oficial):** *"At first match to a rule the path/file name is included or excluded and no further filter rules are processed."* É o **oposto** do gitignore (last-match-wins), origem do bug em que `task.md` subia pro Drive. [rclone.org/filtering](https://rclone.org/filtering/)
- **ISO 8855 vs SAE J670, eixos:** ISO 8855:2011 usa **Y+ à esquerda, Z+ para cima**; SAE J670e (original) usa **Y+ à direita, Z+ para baixo**, incompatíveis, fonte clássica de bug de sinal. O **J670 revisado (2008/2022) é um superset harmonizado** que acomoda ambas as orientações. Prática recomendada: **fixar uma convenção única no projeto (ISO 8855, que é o default de ferramentas modernas tipo MATLAB VDBS) e converter na fronteira** de I/O. [mathworks.com/…/coordinate-systems](https://www.mathworks.com/help/vdynblks/ug/coordinate-systems-in-vehicle-dynamics-blockset.html) · [sae.org/standards/j670_202206](https://www.sae.org/standards/j670_202206-vehicle-dynamics-terminology/)
- **Gitlink órfão:** entrada de submodule sem `.gitmodules` → `git rm --cached <path>` para remover o gitlink dangling (ou recriar `.gitmodules` se o submódulo for legítimo).

**Recomendação:** **Confirmar que a credencial está morta** (Vitor diz que sim → risco baixo); **não reescrever histórico** de um branch já apagado a menos que o commit ainda apareça em cache/fork (checar; se aparecer, `git-filter-repo` + ticket Support). **Padronizar eixos em ISO 8855 com conversão na fronteira** e registrar em ADR curto (regra do v0.1 §8.2). **Corrigir a ordem dos filtros rclone** quando a automação da KB voltar. **Confiança: alta.**

---

# Decisão 6, Artefatos gerados (PDF/HTML de docs) no git

**Pergunta:** versionar os PDF/HTML gerados dos planos, ou tratá-los como build artifact?

**Evidência:**
- **git-scm (oficial):** *"A project normally includes such `.gitignore` files… containing patterns for files generated as part of the project build."* → artefato de build é **a categoria canônica** a ignorar. E: adicionar padrão **não afeta arquivo já trackeado**, para destrackear, `git rm --cached` e depois adicionar ao `.gitignore`. [git-scm.com/docs/gitignore](https://git-scm.com/docs/gitignore)
- **Git LFS** é o caminho sancionado do GitHub para binário que **precisa** ser versionado, mas tem caps por arquivo (2GB Free/Pro) e é quota/billing-metered, não é storage ilimitado.
- **GitHub Releases / Pages** é o canal recomendado para **distribuir** documentos gerados (upload-pages-artifact / deploy-pages), em vez de commitar no histórico.

**Leitura:** o fonte (`.md` + `.css`) é docs-as-code e **deve** ser versionado; o PDF/HTML é reproduzível por `pandoc + chrome --headless` e **é build artifact**. Versionar PDF incha o histórico com binário difícil de diff.

**Recomendação:** **Versionar `.md` + `saru-plan-print.css`; ignorar `output/pdf/*.pdf` e `*.html` gerados** (`.gitignore`). Se um PDF específico precisar ser distribuído, usar **GitHub Release** ou negação explícita `!arquivo.pdf` no `.gitignore` (mais transparente que `git add -f`). Se algum já foi commitado, `git rm --cached`. **Confiança: alta.**

---

# Quadro-resumo para decisão

| # | Decisão | Recomendação | Confiança |
|---:|---|---|---|
| 1 | Batch/DOE | Ligar UI ao real, **reduzir eixos aos 3 vivos** + rótulo honesto | Alta |
| 2 | Segurança pré-beta | **Must-fix** o item estrutural (auth nas rotas do engine + guard async); barato via BFF | Alta |
| 3 | Banda 14-DOF | **Manter** completude+invariantes; sem golden-lap estreito; guard largo opcional | Alta |
| 4 | Scaffold NMPC | **Arquivar** branch (tag) + doc de design; reconstruir incremental na Fase 3 | Média-alta |
| 5 | Segredo + padrões | Credencial morta → sem rewrite (checar cache); ISO 8855 + fix rclone em ADR | Alta |
| 6 | Artefatos no git | Versionar fonte+CSS; **ignorar** PDF/HTML gerados; Release se distribuir | Alta |

---

# Fontes

**Primárias verificadas em 2026-07-10:**
- OWASP API2:2023 Broken Authentication, https://owasp.org/API-Security/editions/2023/en/0xa2-broken-authentication/
- OWASP API8:2023 Security Misconfiguration, https://owasp.org/API-Security/editions/2023/en/0xa8-security-misconfiguration/
- OWASP File Upload Cheat Sheet, https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html
- OptimumG OptimumLap, https://optimumg.com/product/optimumlap/
- Canopy Simulations, Getting Started, https://blog.canopysimulations.com/getting-started-1-sign-in-run-a-study-1ba36089abbd
- VI-grade VI-CarRealTime, https://www.vi-grade.com/en/products/vi-carrealtime/
- TUM Heilmeier et al. (QSS), https://portal.fis.tum.de/en/publications/a-quasi-steady-state-lap-time-simulation-for-electrified-race-car
- TUMFTM/laptime-simulation, https://github.com/TUMFTM/laptime-simulation
- ETH/AMZ MPCC, https://github.com/alexliniger/MPCC · AMZ fssim, https://github.com/AMZ-Driverless/fssim
- GitHub Docs, Removing sensitive data, https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository
- rclone Filtering, https://rclone.org/filtering/
- git-scm gitignore, https://git-scm.com/docs/gitignore
- ISO 8855 / SAE J670 eixos, https://www.mathworks.com/help/vdynblks/ug/coordinate-systems-in-vehicle-dynamics-blockset.html · https://www.sae.org/standards/j670_202206-vehicle-dynamics-terminology/
