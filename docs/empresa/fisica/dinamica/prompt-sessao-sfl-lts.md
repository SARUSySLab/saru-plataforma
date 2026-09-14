---
titulo: "Prompt de sessão, SFL / LTS (simulação e setup)"
data: "2026-08-22"
origem: "_arquivo/saru-app/docs/execution/PROMPT-sessao-sfl-lts.md"
status: "stale"
area: "dinamica_veicular"
---

# Prompt de sessão, SFL / LTS (simulação e setup)

> **[2026-08-22] Sessão ainda NÃO rodou** ("Libra Inicial" segue em
> `LtsSetupView.tsx:320`). **Errata do item 3:** o dono do número pt-BR JÁ chegou aqui, > `LtsSetupView.tsx` importa `formatNumber` e usa em 12 pontos (`867c414`). O item 2
> (categoria) conversa com a branch `feature/claude-category-templates-design`.

> Criado 2026-08-16 a pedido do Vitor: *"gere o prompt de sessão específico para voltar a
> mexer nisso"*, sobre `/sfl`, depois de `/sd` ficar congelado (*"se for pra mexer em
> simulação mexe no LTS/SFL"*).
> **Cole o bloco da §1 numa sessão nova, na raiz de `saru-app`.** O resto é o terreno
> medido em 2026-08-16, confira antes de confiar, o repo anda.

---

## 1. O bloco para colar

```
Sessão nova no saru-app, frente SFL/LTS (simulação e setup). O /sd está CONGELADO por
decisão do Vitor (2026-08-16): simulação mexe aqui, não lá.

LEIA ANTES, nesta ordem:
  docs/audit/2026-08-16-passeio-hub-logado.md        achados 16 e 17 são desta tela
  docs/execution/2026-08-16-direcao-pos-passeio.md   §D4 (o que ficou congelado e por quê)
  docs/adr/0042-borda-de-exibicao-unidades-paddock.md  a borda de unidades já tem ADR

Terreno: rota /sfl → features/lts/views/LtsView.tsx (27 linhas) monta o workspace.
2.285 linhas de view no total, concentradas em 3 arquivos:
  LtsSetupView.tsx        693   a tela que o piloto vê primeiro
  LtsSimulatorView.tsx    590
  LtsDataAnalysisView.tsx 471
A física mora em features/lts/model.ts, 3 funções, e só 4 testes em model.test.ts:
  computeTireThermo(pressurePsi, trackTemp, camberDeg)
  computeAero(...)
  wireChannelsToSimulatedLap(...)

⚠️ REGRA DURA: `model.ts` é FÍSICA. Qualquer mudança em fórmula, parâmetro ou faixa exige
aprovação explícita do Vitor ANTES de escrever, cerimônia de 4 seções, sem exceção.
Mexer em rótulo, unidade exibida, cor e layout NÃO é física e segue o fluxo normal.

O que está aberto, do mais barato ao mais caro:

1. TERMINOLOGIA (barato, zero física)
   - "COLD INFLATION PRESSURE (LIBRA INICIAL)" e "ESTIMATED HOT PRESSURE (LIBRA FINAL)":
     rótulo em inglês com parêntese em português, dentro de tela cujo subtítulo é
     português ("Configure setups de veículo e propriedades aerodinâmicas").
   - "libra" NÃO é a unidade. psi = libra-força por polegada quadrada; libra sozinha é
     força. O rótulo ensina errado ao piloto.
   - A tela inteira é assim: SUBSYSTEMS, TIRES, POWERTRAIN (ICE), DRIVER MODEL,
     TIRE SIMULATION CALIBRATION, CHASSIS & GEOMETRY.

2. CATEGORIA DOS PRESETS (barato, é dado)
   ACTIVE VEHICLE PRESET traz "Carro de Rua / Track Day (Gol/Onix 1.0T) (GT3)" e
   "Stock Car SNG1 (V8) (GT3)". A categoria virou rótulo-lixo cobrindo do hatch 1.0 à
   Stock Car. Decidir se a categoria some ou se ganha valor certo por preset.

3. SEPARADOR DECIMAL (barato, mas é sistêmico, combine com quem estiver na frente D1)
   36.3 psi · 42.9 psi · -3.2 ° · 12.0 km/h. A regra está escrita em lib/format.ts:10
   ("Separador decimal é VÍRGULA: o produto é pt-BR") e o TracksideView a cumpre em 5
   pontos. Aqui não cumpre em nenhum.

4. A FAIXA IDEAL QUE A TELA CONTRADIZ (precisa do Vitor, é física)
   A tela mostra ESTIMATED HOT PRESSURE 42.9 psi e, embaixo, "Ideal Hot Range: 29.5 -
   31.5 psi". 11 psi fora da faixa que ela mesma declara, sem um aviso. Ou o preset está
   errado, ou a faixa está, ou falta o alerta, as três saídas são decisão dele, não do
   agente. NÃO ajuste computeTireThermo para "fechar" o número.

5. COBERTURA (médio)
   4 testes para 3 funções de física. computeTireThermo é o que produz o número da
   pressão quente que o piloto lê e acredita.

Regras que valem sempre: cerimônia de 4 seções antes de tarefa não-trivial; número nunca
inventado (valor exibido sai de sample real do repo, processado pelo engine de verdade);
tempo em m:ss,mmm; commit atômico; nada de push sem ordem do Vitor. `services/frontend/**`
pode ter sessão de design viva, cheque com ListAgents antes de escrever.
```

---

## 2. Por que esta frente existe

`/sd` (Vehicle Editor / SARU Dynamics) tinha o achado mais grave de unidade do passeio, card em `N/mm`, `mm` e `kN/m` contra formulário em `N/m` e `m`, fator 1000 sem conversão
declarada. O Vitor congelou `/sd` e mandou a simulação para cá. **O achado do `/sd` fica
registrado** em `docs/audit/2026-08-16-passeio-hub-logado.md` §P1-4 e é o primeiro item
quando aquela rota voltar.

## 3. O que NÃO fazer nesta frente

- **Não** "consertar" número de física para bater com faixa exibida. Se o número diverge da
  faixa, o achado é a divergência, quem decide qual lado muda é o Vitor.
- **Não** migrar `/sd` de carona. Está congelado por decisão, não por esquecimento.
- **Não** tratar `libra`→`psi` como troca de string solta: a mesma confusão pode estar em
  `model.ts` (o parâmetro chama-se `pressurePsi`, o que sugere que o **código** está certo e
  só o **rótulo** mente, confirme antes).

## 4. Cruzamentos com outras frentes

| esta frente toca | dona | cuidado |
|---|---|---|
| separador decimal | D1 da direção pós-passeio | mesma correção em 9+ arquivos; não faça sozinho um padrão diferente |
| cor de comparação | D1 | `LtsSetupView.tsx:335` e `:496` usam `--saru-ok`/`--saru-warn` como semáforo de faixa, é uso legítimo (estado), **não** é o par ganho/perda. Não migre para `--saru-delta-*` |
| unidades exibidas | ADR-0042 (borda de exibição) | a ADR já existe; leia antes de inventar convenção |
