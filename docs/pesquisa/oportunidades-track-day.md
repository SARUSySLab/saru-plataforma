---
titulo: "Oportunidades de Produto, Track Day BR (derivado da pesquisa 2026-07)"
data: "2026-08-11"
origem: "_arquivo/saru-app/docs/product/oportunidades-track-day.md"
status: "vigente"
area: "produto"
---

# Oportunidades de Produto, Track Day BR (derivado da pesquisa 2026-07)

> **Status:** exploração 2026-07-13, para priorização. Cada oportunidade cita o fato da
> pesquisa que a sustenta (`docs/research/2026-07-pistas-e-track-days.md` = [P],
> `2026-07-aquisicao-de-dados.md` = [A]). Personas em
> `docs/product/personas-e-modularidade.md`.

## Leitura de mercado (o que a pesquisa diz que mudou)

1. **Brasília reabriu (11/2025) e não existe base de referência**, pista nova de 5.384 m,
   cena de TD nascendo agora (Distrito Racing, Union Meet, BTS com 800 vagas/temporada) e
   **zero tempos públicos de carros de rua** [P§1]. Quem construir a base de referência de
   BSB primeiro vira o padrão da praça.
2. **Track day brasileiro não tem cronometragem oficial**, o amador se mede sozinho, por
   celular/RaceBox [P§4]. Ou seja: o dado existe, é dele, e não tem onde virar análise.
3. **As 3 pistas estão em transição de asfalto** (Interlagos 2024 ondulado; BSB verde;
   Goiânia refeita out/2026) [P§1-3], tempos históricos valem pouco; contexto de condição
   vale muito.
4. **O ecossistema de dados converge para formatos que já lemos ou são baratos de ler**
   (.ld/.ldx dos sims, .vbo/.csv dos apps de GPS, Pi ASCII na Cup) [A§5-7].

## Oportunidades (ranqueadas por alavancagem/esforço)

### O1 · "Quanto faz meu carro?", calculadora pública de volta ideal (aquisição)
Landing aberta: escolhe pista (Interlagos/BSB/Goiânia) + carro (tiers S/P) + condição
(TD tarde/manhã) → volta ideal simulada + delta vs referências de categoria (F1 1:09.5 ·
Cup 1:33.8 · recorde de rua 1:36.9 em Interlagos) [P§2]. É o gancho viral pré-evento; coleta
e-mail + região. **Depende de:** Tier S nº 1 no core; tabela de referências (pronta na
pesquisa). Esforço M.

### O2 · Relatório pós-track-day compartilhável (retenção + viral)
Upload do RaceChrono/RaceBox (.vbo/.csv [A§6]) ao voltar do evento → relatório de 1 página:
melhor volta, consistência, mapa de onde perde tempo, delta vs volta ideal simulada, evolução
vs evento anterior, com card de compartilhamento. É o "Strava do track day"; o formato de TD
(baterias, sem cronometragem oficial [P§4]) deixa esse vazio exatamente. **Depende de:**
reader `.vbo` (esforço B [A§7]). Esforço M.

### O3 · Base de referência comunitária por pista/condição (moat)
Cada upload alimenta (anonimizado, opt-in) a curva de tempos por classe de carro × pista ×
condição de asfalto. Resolve a lacuna que a pesquisa encontrou (sem tempos públicos de rua em
BSB; Goiânia zerada em out/2026 [P§1,3]) e cria o ativo que ninguém copia rápido. Percentil
("você está no top 20% dos Golf GTI em Interlagos") é feature paga natural. Esforço M
(agregação + curadoria), valor A.

### O4 · Modo evento: simulação de bateria, não de volta (diferencial técnico)
TD real = baterias de 20-30 min, tráfego, pneu de rua aquecendo/degradando, freio em fade
[P§4-5]. Simular a BATERIA (volta ideal → aquecimento → janela ótima → degradação) responde o
que o amador vive: "em qual volta da bateria sai meu tempo?" e "quanto o tráfego me custou?".
Nenhum concorrente amador faz isso. **Depende de:** knob de grip/térmica no core (auditoria
`audit-saru-core.md` §4). Esforço A, diferencial A.

### O5 · Assistente de pressão de pneu (psi) por bateria (utilidade imediata)
Organizadores aferem/calibram pneu no grid [P§4]; pressão é O ajuste universal do Tier S.
Recomendação: pressão fria alvo por carro/pneu/pista/temperatura + registro do que foi usado
por bateria, correlacionado com os tempos (dados do O2). Esforço B-M, valor imediato p/ P1.

### O6 · Pacote organizador (B2B, Distrito Racing, Crazy for Auto, BTS)
Os organizadores já operam grupos por nível/potência e Time Attack recreativo [P§4]; oferecer
telemetria/relatórios white-label por inscrito (QR no briefing), ranking recreativo por
classe e dashboard do evento. BTS/2026 sozinho = 800 inscrições/temporada em BSB [P§1].
Canal de distribuição, não feature. Esforço M (multi-tenant/workspaces é pré-requisito, personas §2.4).

### O7 · Ponte sim→pista (aquisição barata, dados abundantes)
Mesmo carro/pista no GT7/ACC vs vida real: "seu 1:52 no GT7 vale ~1:58 em Interlagos de
verdade", a cadeia de ingestão já existe (.ld/.ldx via sim-to-motec/ACC nativo [A§5]) e o
fator sim→real vira pesquisa nossa. Puxa a persona P5 para o evento presencial (LTV cross).
**Depende de:** parser `.ldx` (esforço B, prioridade nº 1 [A§7]). Esforço B-M.

### O8 · Radar de condições e eventos por praça (conteúdo/SEO)
Página viva por pista: estado do asfalto (Goiânia reabre out/2026 [P§3]), calendário de TD
(Sympla/Autoclubes), clima típico, altitude e o que isso faz com o carro [P§5]. Barato,
recorrente, indexável, e alimenta o simulador com a condição do dia. Esforço B.

## Sequência sugerida (encadeia com o roadmap técnico)

1. **Agora** (destrava várias): reader `.vbo` + parser `.ldx` [A§7 itens 1-2] → O2 e O7.
2. **Curto prazo**: O5 (pressão psi) + O8 (radar), valor visível com pouca física nova.
3. **Médio**: O1 (precisa do Tier S nº 1) e O3 (precisa de volume do O2).
4. **Depois**: O4 (física de bateria) e O6 (precisa de workspaces).

## Riscos honestos

- O3/O6 dependem de volume, sem O2 rodando bem, viram vitrine vazia.
- Fator de grip TD (0,90-0,95) é heurística sem fonte [P§5], calibrar com os primeiros
  dados reais antes de exibir como número.
- Goiânia: qualquer conteúdo/preset é provisório até o asfalto definitivo (out/2026) [P§3].
