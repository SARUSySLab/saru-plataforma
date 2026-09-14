---
titulo: "Racelogic VBOX, o que é, o que dá para aproveitar, e como falar com eles"
data: "2026-08-11"
origem: "_arquivo/saru-app/docs/research/2026-07-29-racelogic-vbox.md"
status: "vigente"
area: "telemetria"
---

# Racelogic VBOX, o que é, o que dá para aproveitar, e como falar com eles

> **Resgatado em 2026-08-04** de `claude/saru-umbrella-docs-architecture-6s85d2` (nunca
> mergeada) pela sessão de higiene. O código daquela branch foi superseded, só o documento
> sobreviveu. **Conteúdo NÃO re-verificado nesta sessão:** as referências de commit e as
> afirmações sobre o código valem para a data do cabeçalho acima, não para hoje.

> Pesquisa de 2026-07-29. **Limite de evidência declarado:** o *support centre* da Racelogic
> (`en.racelogic.support`, `racelogic.support`) e as páginas de produto do `vboxmotorsport.co.uk`
> respondem **403 a fetch automatizado**. O que está aqui vem dos **trechos indexados** dessas
> mesmas páginas e das páginas que respondem. Nada abaixo foi verificado abrindo o software.
> Onde a fonte é fraca, está dito.

---

## 1. Por que isto importa agora

O engine **já lê `.vbo`**: `services/telemetry-api/saru_lapanalyzer/infra/datasources/vbo_file.py`
é um parser dedicado, com perfil `vbox` no `aliases.yaml`. Ele trata três particularidades do
formato que só quem abriu arquivo real conhece:

- o canal `time` do VBOX é **hora GPS do dia** (`HHMMSS.sss`), não segundo decorrido, o parser
  sintetiza o eixo somando `sampleperiod`;
- o VBOX loga `VBOX_lapnumber`, então a segmentação de voltas **não precisa** do fallback por
  distância que os `.ld` exigem;
- `lat`/`long` vêm em **minutos de arco**, convenção West-positivo, convertidos no alias.

Ou seja: a integração técnica com o ecossistema VBOX **já está de pé** e é a mais barata do
catálogo de formatos. Isso muda a conversa com a Racelogic de "poderíamos integrar" para
"já lemos o formato de vocês".

## 2. O que é cada coisa (não confundir)

| Produto | O que é | Relevância p/ SARU |
|---|---|---|
| **VBOX Sport / Touch** | Data logger GPS autônomo, à prova d'água, grava em cartão SD | Hardware, fonte de `.vbo` |
| **Circuit Tools** | Software de análise (Windows, macOS e iOS), é o "i2 da Racelogic" | **Benchmark de UX**, §3 |
| **VBOX Sim / Sim Pack** | Captura dados e vídeo de jogos de corrida e converte para dado VBOX, para analisar no Circuit Tools | **Concorrente direto** do nosso eixo GT7/sim, §4 |
| **VBOX LapTimer** | Display de feedback instantâneo no carro | Fora do escopo |

**VBOX Sim suporta:** rFactor, rFactor 2, Project CARS 1/2, Assetto Corsa, ACC, F1 2017-2021,
iRacing e RaceRoom. **Note o que falta: Gran Turismo 7.** É exatamente o nicho onde já operamos
(ADR-0015, gateway GT7 local-first).

## 3. As features boas, e o que vale copiar

### 3.1 O modelo de seleção de voltas ⭐ (o mais importante)

O Circuit Tools resolve "comparação" **como dimensão, não como tela**:

- O painel de voltas tem uma coluna **"Show"** com *checkbox por volta*, marcar exibe aquela volta
  no **gráfico, no mapa e no vídeo** simultaneamente.
- Há uma coluna **"Ref"**: a volta de referência é, por padrão, a mais rápida do arquivo, e o
  usuário troca marcando outra.
- **Todos os splits, comparações de tempo e valores de Delta-T são relativos à referência escolhida.**
- Cada volta tem cor própria, trocável clicando no retângulo colorido.

Não existe uma "tela de comparação" no Circuit Tools, **toda tela já é comparativa**, porque a
seleção de voltas é global. Isto valida diretamente a leitura do Vitor de que o nosso `/sa/compare`
não deveria ter destaque de primeiro nível. Spec derivada:
[`../product/spec-multivolta-sa-2026-07-29.md`](../product/spec-multivolta-sa-2026-07-29.md).

### 3.2 Ideal Lap e Multi Lap

- Ideal Lap: volta teórica montada com o melhor de cada setor **da sessão**, exibida no fim da
  tabela de voltas como se fosse mais uma volta.
- Multi Lap: o mesmo, mas **entre arquivos**, só é gerada quando dois ou mais arquivos são
  carregados juntos.

Elegante: as duas entram na lista de voltas como cidadãs de primeira classe, então tudo que compara
volta já as compara de graça. Nós temos `ideal_lap_time` no `SessionSummary` do engine, **como
número solto**, não como volta selecionável.

### 3.3 Setores como camada de leitura

Os setores são **marcados no gráfico**, não só na tabela, para facilitar casar posição entre gráfico
e mapa. A tabela de setores colore a célula pela comparação com a referência.

### 3.4 Vídeo com moldura semântica

Na comparação com vídeo, **a volta mais rápida ganha borda verde e a mais lenta borda vermelha**.
Custo de implementação ~zero, ganho de leitura alto, o tipo de detalhe que separa ferramenta de
piloto de ferramenta de engenheiro.

### 3.5 Predição de lap time ao vivo

No logger, delta-t contra a referência num gráfico de barras vermelho/verde, com previsão do tempo
final da volta em curso. É a versão "no carro" do nosso Δ, relevante se o `telemetry-live` evoluir.

### 3.6 Posicionamento declarado

*"Designed by racing drivers, for racing drivers, with none of the complexity normally associated
with data analysis software."* É a mesma tese do nosso P3/amador, a diferença é que eles chegaram
por simplificação de ferramenta de engenheiro e nós chegamos por interpretação (as 3 perguntas).

## 4. Leitura competitiva honesta

**Onde eles são mais fortes:** hardware próprio + software + vídeo sincronizado num pacote só,
multiplataforma (inclusive iOS), marca estabelecida desde 1992, rede global de distribuidores.

**Onde temos espaço:**

1. **GT7 não está na lista de sims suportados**, e é onde temos gateway próprio.
2. **Circuit Tools é desktop/app; nós somos web**, nada para instalar, análise compartilhável por
   link. (Reconhecer o custo: eles têm vídeo sincronizado, nós não.)
3. **Física de referência.** Eles comparam você com você (ou com outro piloto). Nós comparamos com
   uma **volta simulada por solver validado**, o overlay `simReference`. Isso não existe no
   Circuit Tools e é o nosso diferencial menos copiável.
4. **Interpretação.** Eles entregam o dado bem organizado; a leitura é do piloto. Nós entregamos
   "onde você perdeu, por quê, o que treinar".

**Onde estamos atrás e não adianta fingir:** vídeo sincronizado, predição ao vivo no carro, e
maturidade de plataforma.

## 5. Caminhos de parceria, do mais barato ao mais ambicioso

| # | Movimento | O que exige de nós | Risco |
|---|---|---|---|
| 1 | **Suporte a `.vbo` como feature declarada**, "importe direto do seu VBOX" | Já funciona; falta rótulo na UI de importação e um `.vbo` real na suíte de fixtures | ~zero. É o passo óbvio e deveria sair antes de qualquer contato |
| 2 | **Contato técnico**, avisar que lemos `.vbo` e perguntar sobre spec oficial do formato / validação | 1 e-mail + arquivo de exemplo | baixo |
| 3 | **Distribuidor/revenda no Brasil**, a rede deles não mostra distribuidor brasileiro nas páginas indexadas | Estrutura comercial que ainda não temos | médio, vira operação de hardware |
| 4 | **Integração de saída**, exportar nossa análise em `.vbo` para abrir no Circuit Tools | Escrever o writer (o parser já ensina o formato) | baixo técnico, valor incerto |
| 5 | **Complemento, não concorrente**, posicionar o SARU como a camada de *interpretação e física* sobre o dado VBOX | Narrativa comercial + prova com dado real | é a aposta mais interessante e a que precisa do Vinícius |

> ⚠️ **Verificar antes do item 1:** não temos `.vbo` real na suíte. O parser existe, mas
> `tests/fixtures/real_samples/` não lista nenhum VBOX. Declarar suporte sem um arquivo real
> ingerido violaria a regra do produto ("só prometemos o que o código sustenta").

## 6. Como falar com eles

- **Sede (UK):** Racelogic Ltd, Unit 10, Swan Business Centre, Osier Way, Buckingham, MK18 1TB,
  Reino Unido · tel. **+44 1280 823803**.
- **Escritórios regionais:** Reino Unido, Estados Unidos e Alemanha, além da rede global de
  distribuidores.
- **Página de contato do braço motorsport:** <https://www.vboxmotorsport.co.uk/en/contact>
- **Distribuidores:** <https://vboxmotorsport.co.uk/index.php/en/distributors-worldwide>, a
  Racelogic diz que, se o país não estiver listado, o caminho é a sede do Reino Unido. **Não
  encontrei distribuidor brasileiro** nas páginas indexadas; confirmar na página de distribuidores.
- Eles publicam um caminho explícito para **"tornar-se trader ou distribuidor VBOX Motorsport"**, é a porta formal do item 3 da tabela acima.

**Sugestão de abordagem (item 2, o de menor atrito):** e-mail técnico curto ao suporte motorsport
dizendo que (a) já lemos `.vbo` num produto web de análise, (b) mostramos um relatório gerado de um
arquivo VBOX real, (c) perguntamos se há especificação oficial do formato e se há interesse em
conversar sobre complementaridade. Suporte técnico costuma responder mais rápido que comercial, e a
resposta já revela se existe apetite institucional.

---

## Fontes

- [VBOX Sport, VBOX Motorsport](https://vboxmotorsport.co.uk/index.php/us/vbox-sport-lightweight-performance-meter-and-lap-timer)
- [Circuit Tools, VBOX Motorsport](https://www.vboxmotorsport.co.uk/us/circuit-tools)
- [Circuit Tools 3, View Layout (Racelogic Support)](https://en.racelogic.support/VBOX_Motorsport/Software_Info/Circuit_Tools/Circuit_Tools_3/User_Guide/03_View_Layout)
- [Circuit Tools 3, Quick Start Guide](https://en.racelogic.support/VBOX_Motorsport/Software_Info/Circuit_Tools/Circuit_Tools_3/Quick_Start_Guide)
- [How to Use Circuit Tools to Become Faster](https://en.racelogic.support/VBOX_Motorsport/Software_Info/Circuit_Tools/Knowledge_Base/How_to_Use_Circuit_Tools_to_Become_Faster)
- [VBOX Sim Lite](https://www.vboxmotorsport.co.uk/index.php/en/vbox-sim)
- [VBOX Sim, Overview (Racelogic Support)](https://en.racelogic.support/VBOX_Motorsport/Software_Info/VBOX_Sim)
- [Hands-on with Racelogic's VBOX Simulator Software, Traxion](https://traxion.gg/hands-on-with-racelogics-vbox-simulator-software/)
- [A Look At The RaceLogic VBOX SIM Data Analyzer Software, Bsimracing](https://www.bsimracing.com/a-look-at-the-racelogic-vbox-sim-data-analyzer-software/)
- [Where to Buy Racelogic Products](https://en.racelogic.support/Knowledge_Base/Where_to_Buy_Racelogic_Products)
- [Contato, VBOX Motorsport](https://www.vboxmotorsport.co.uk/en/contact)
- [Distribuidores mundiais, VBOX Motorsport](https://vboxmotorsport.co.uk/index.php/en/distributors-worldwide)
- [Racelogic, Wikipedia](https://en.wikipedia.org/wiki/Racelogic)
