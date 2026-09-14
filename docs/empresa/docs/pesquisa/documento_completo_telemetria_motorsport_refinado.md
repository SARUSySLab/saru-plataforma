---
titulo: "Telemetria de Motorsport para Track Day, Kart, Moto, Carro e Simulação"
data: "2026-08-11"
origem: "_arquivo/saru-app/docs/research/documento_completo_telemetria_motorsport_refinado.md"
status: "vigente"
area: "telemetria"
---

# Telemetria de Motorsport para Track Day, Kart, Moto, Carro e Simulação
## KPIs, progressão, interfaces, run sheets, setup e arquitetura de produto

**Versão:** pesquisa refinada em 08/08/2026  
**Escopo:** software de análise para pilotos amadores, track day, kart, moto, turismo, GT3, protótipo, fórmula e simuladores como GT7, iRacing e ACC.

---

## 0. Resposta executiva

Não existe um padrão universal que defina todos os KPIs, a hierarquia de dados ou o formato de run sheet usado por equipes de automobilismo. O que existe é uma convergência operacional:

- volta, setor, micro-setor e curva como unidades de análise;
- tempo de volta, delta e ritmo repetível;
- velocidade, frenagem, acelerador, trajetória e aceleração;
- estado dos pneus, combustível, temperatura e confiabilidade;
- configuração do carro e rastreabilidade de cada mudança;
- feedback do piloto associado à telemetria;
- comparação contra uma referência física e contextualizada.

A recomendação central para o produto é separar cada métrica em quatro níveis:

1. **Medida:** canal diretamente adquirido.
2. **Derivada:** cálculo matemático sobre canais.
3. **Prática de equipe:** convenção operacional recorrente.
4. **Interpretação:** score ou recomendação dependente de regras.

Isso impede que termos como “aproveitamento de grip”, “qualidade de frenagem” ou “setup ideal” sejam apresentados como padrões universais quando, na realidade, são definições de engenharia ou heurísticas configuráveis.

---

## 1. O que foi pesquisado e grau de confiança

### 1.1 Documentação oficial de software

A documentação oficial foi usada principalmente para verificar como as ferramentas organizam dados e quais funções oferecem:

- MoTeC i2: logs, canais, voltas, beacons, detalhes e workbooks. [web:16][web:92]
- AiM Race Studio 3: database, eventos, sessões, canais, voltas e seleção de conjuntos de voltas. [web:17][web:24][web:90][web:91]
- AiM predictive reference lap: melhor volta da sessão, melhor volta do dia, volta anterior ou volta salva. [web:94]
- Garage61: melhor volta, optimal lap, ghost lap, telemetria associada, eventos e equipes. [web:89]
- RaceLab: overlay de inputs e comparação com volta de referência. [web:52]
- Cosworth Pi Toolbox: materiais de uso, workbooks e análise de voltas. [web:25][web:26]

### 1.2 Referências técnicas e acadêmicas

Foram consultados trabalhos e materiais técnicos para verificar métricas de desempenho e métodos quantitativos:

- análise de padrões de frenagem, acelerador, direção e velocidade em simulador profissional; [web:76]
- uso de variação estatística dos tempos de volta para consistência; [web:80]
- métricas e técnicas de condução associadas a lap time, incluindo trail braking, steering, oversteer e desvio de linha; [web:78]
- análise de frenagem por esforço, agressividade, soltura e consistência; [web:4][web:5]
- métricas de track day como melhor volta, consistência, grip, coasting e velocidade por curva. [web:1]

### 1.3 Templates e prática operacional

Templates públicos de setup sheet e run sheet foram usados como evidência de campos recorrentes, não como prova de um padrão oficial:

- setup sheets com pista, data, sessão, clima, combustível, pneus, suspensão, alinhamento, pesos e notas; [web:42][web:88]
- run sheets de equipes com pista, data, horário, número da tomada e condições ambientais. [web:36]
- o formato exato depende da categoria, do carro, da duração do teste, da equipe e do objetivo da sessão.

### 1.4 Limitações da evidência

Não foi encontrada uma norma única de uma federação ou associação que prescreva todos os campos de uma run sheet para “track day” em geral. Também não é possível concluir, apenas pela documentação pública, que todas as equipes profissionais usam a mesma hierarquia de campeonato, etapa, sessão e volta.

As seções deste documento distinguem explicitamente:

- **padrão publicado/documentado:** função ou estrutura confirmada na fonte;
- **prática recorrente:** convenção observada em materiais, ferramentas e engenharia de pista;
- **recomendação de produto:** proposta para o seu software;
- **heurística:** métrica interpretativa que precisa ser documentada e validada.

---

# Parte I, KPIs pós-sessão

## 2. Princípio de seleção de KPI

Um KPI deve responder a pelo menos uma destas perguntas:

- O piloto está mais rápido?
- Ele consegue repetir o desempenho?
- Em qual curva o tempo está sendo perdido?
- A perda vem de frenagem, rotação, tração ou linha?
- A mudança de setup produziu o efeito esperado?
- O pneu, combustível ou tráfego alterou a comparação?
- O resultado é confiável ou foi uma volta isolada?

Uma boa interface deve apresentar primeiro uma decisão e depois os canais que justificam essa decisão.

### 2.1 Camadas

| Camada | Exemplos | Status |
|---|---|---|
| Medida | velocidade, pressão, posição de pedal, GPS, temperatura, RPM | canal adquirido |
| Derivada | ponto de frenagem, apex, throttle pickup, theoretical lap | cálculo documentado |
| Prática de equipe | brake quality, sustainable pace, setup window | convenção operacional |
| Interpretada | confiança, eficiência, aproveitamento de grip, recomendação | score/heurística |

---

## 3. KPIs para piloto amador

O piloto amador normalmente precisa de uma resposta simples e acionável, não de um workbook com centenas de canais.

### 3.1 Painel recomendado

- melhor volta limpa;
- média das melhores voltas;
- ritmo sustentável;
- consistência;
- delta por setor, micro-setor e curva;
- ponto de frenagem;
- distância de frenagem;
- velocidade mínima;
- velocidade de saída;
- tempo até começar a acelerar;
- coasting;
- suavidade de freio e acelerador;
- aceleração lateral e longitudinal;
- voltas válidas e inválidas;
- tráfego e flags;
- comentário subjetivo do piloto.

### 3.2 Pergunta da interface

A interface deve responder:

> “Onde perdi tempo e qual comportamento devo testar na próxima volta?”

A recomendação não deve ser genérica, como “seja mais rápido”. Deve ser contextual, por exemplo:

- “Na curva 4, você freou 8 m antes da sua referência e perdeu 0,12 s até o apex.”
- “A saída está 3 km/h mais lenta porque o throttle chegou a 50% 0,4 s depois.”
- “Sua volta mais rápida não foi repetida; o ritmo das cinco melhores voltas está 0,42 s acima dela.”

Ferramentas voltadas a pilotos usam comparação de zonas de frenagem, pressão máxima, trail braking, delta e setores. [web:2][web:13]

---

## 4. KPIs para piloto avançado

O piloto avançado precisa distinguir falta de velocidade de falta de repetibilidade.

### 4.1 Ritmo

- melhor volta limpa;
- theoretical lap;
- sustainable pace;
- repeatability gap;
- potencial por setor;
- dispersão por curva;
- sensibilidade a combustível e pneu.

### 4.2 Frenagem

- lift-off;
- início do freio;
- pico de pressão;
- tempo até o pico;
- distância e duração da frenagem;
- pressão residual no turn-in;
- velocidade de entrada;
- suavidade da soltura;
- erro do ponto de frenagem;
- lock-up ou ABS;
- desaceleração e jerk.

### 4.3 Rotação e saída

- velocidade mínima;
- posição do apex;
- yaw rate;
- tempo até 25%, 50%, 80% e 100% de acelerador;
- velocidade a 20, 50 e 100 m da saída;
- wheelspin;
- correção de direção;
- coasting;
- tempo de aceleração sustentada.

### 4.4 Linha e controle

- distância até a borda da pista;
- repetibilidade da trajetória;
- steering rate;
- amplitude e frequência das correções;
- relação entre linha e velocidade;
- oversteer/understeer estimado, se os canais permitirem.

Estudos de comportamento de condução em simulador profissional analisam explicitamente frenagem, throttle, steering e velocidade, e utilizam variações estatísticas em janelas temporais para caracterizar padrões de condução. [web:76]

---

## 5. KPIs para engenheiro de pista

O engenheiro precisa conectar o comportamento do piloto ao estado do veículo, às condições e ao setup.

### 5.1 Desempenho

- lap time;
- sector time;
- micro-sector time;
- theoretical lap;
- delta contra referência;
- delta entre pilotos;
- desempenho por curva;
- potencial versus ritmo repetível;
- tempo perdido por erro, tráfego ou condição.

### 5.2 Driver controls

- steering angle;
- steering rate;
- throttle;
- brake pressure;
- brake bias;
- gear;
- RPM;
- clutch;
- TC;
- ABS;
- engine map;
- differential controls.

### 5.3 Dinâmica do veículo

- velocidade;
- aceleração longitudinal e lateral;
- aceleração resultante;
- yaw rate;
- roll e pitch;
- slip angle estimado;
- wheel speed;
- slip ratio;
- ride height;
- suspensão e amortecedores;
- bottoming;
- carga aerodinâmica estimada;
- temperatura e pressão dos pneus.

### 5.4 Sistema e confiabilidade

- temperatura de água, óleo, motor e bateria;
- temperatura de freio;
- combustível consumido;
- pressão de combustível;
- tensão elétrica;
- sensores inválidos;
- perda de GPS;
- sincronização;
- canais saturados;
- flags de diagnóstico;
- qualidade da amostra.

### 5.5 O KPI de engenharia

O objetivo não é encontrar somente a volta mais rápida. É avaliar:

> “O carro, o pneu, o piloto e as condições permitiram repetir esse desempenho dentro da janela operacional?”

---

# Parte II, Métricas de progressão

## 6. Preparação dos dados antes do cálculo

Nenhuma métrica de progressão é confiável sem uma política explícita de inclusão e exclusão.

### 6.1 Excluir ou marcar

- out-laps;
- in-laps;
- pit-laps;
- voltas com bandeira amarela;
- tráfego significativo;
- corte de pista;
- erro ou excursão;
- chuva ou mudança brusca de aderência;
- volta com pneu ou combustível fora da condição comparável;
- perda de GPS;
- falha de sensor;
- sessão com setup alterado no meio, salvo se o objetivo for comparar a alteração.

### 6.2 Metadados mínimos

Cada volta deve carregar:

- evento;
- data/hora;
- pista e configuração;
- piloto;
- veículo;
- categoria;
- sessão/run;
- pneu e ciclo;
- combustível estimado;
- setup revision;
- condição de pista;
- tráfego;
- validade;
- motivo de exclusão;
- qualidade de GPS e sensores.

---

## 7. Consistência

Para tempos de volta válidos \(t_i\):

\[
\bar{t}=\frac{1}{N}\sum_{i=1}^{N}t_i
\]

\[
\sigma_t=\sqrt{\frac{1}{N-1}\sum_{i=1}^{N}(t_i-\bar{t})^2}
\]

Indicadores possíveis:

- desvio-padrão em segundos;
- intervalo interquartil, \(P_{75}-P_{25}\);
- intervalo entre percentis, \(P_{90}-P_{10}\);
- coeficiente de variação, \(CV=\sigma_t/\bar{t}\);
- porcentagem dentro de uma tolerância, como ±0,3 s da mediana;
- maior erro absoluto contra a mediana;
- tendência de degradação ao longo do stint.

O intervalo interquartil é útil quando existe uma volta anormal com tráfego ou erro. O desvio-padrão é simples e interpretável, mas sensível a outliers.

A consistência deve ser calculada por sessão e também em janelas móveis, por exemplo:

- primeiras cinco voltas válidas;
- melhores cinco voltas;
- últimas cinco voltas;
- stint completo;
- mesmas condições em várias etapas.

A seleção de “melhores N”, “primeiras N”, “últimas N” e melhores N por setor também é oferecida pelo Race Studio 3 para diferentes objetivos de análise. [web:91]

---

## 8. Ritmo sustentável e ritmo contra a melhor volta

### 8.1 Definições

- **Best lap:** melhor volta real, contínua e válida.
- **Theoretical lap:** combinação dos melhores setores ou micro-setores.
- **Sustainable pace:** mediana ou média das melhores \(K\) voltas comparáveis.
- **Reference lap:** volta escolhida como referência operacional.
- **Session pace:** distribuição das voltas válidas da sessão.

### 8.2 Repeatability gap

Uma definição simples:

\[
\Delta_{repeat}=t_{best}-median(t_{best\ K})
\]

Outra alternativa, mais intuitiva para mostrar perda relativa:

\[
G_{repeat}=median(t_{best\ K})-t_{best}
\]

Quanto menor o valor, mais próximo o piloto está de repetir sua melhor volta.

### 8.3 Potential gap

\[
\Delta_{potential}=t_{best}-t_{theoretical}
\]

Se o theoretical lap for muito mais rápido que qualquer volta real, isso pode indicar:

- setores rápidos obtidos em voltas diferentes;
- falta de consistência;
- referência contaminada por condições diferentes;
- segmentação ruim;
- mudança de setup ou pneu;
- tráfego localizado.

Por isso, o theoretical lap deve exibir sua composição e não ser tratado automaticamente como uma volta possível.

### 8.4 Progressão entre sessões

Para comparar sessões, use pelo menos três curvas:

1. melhor volta;
2. ritmo sustentável;
3. consistência.

Uma progressão saudável pode ser:

- melhor volta reduzindo;
- ritmo sustentável reduzindo;
- dispersão reduzindo ou permanecendo estável;
- menor dependência de uma volta isolada;
- maior repetibilidade por curva.

Uma melhora de melhor volta com piora grande da consistência deve ser classificada como “mais rápido, menos controlado”, não simplesmente como progresso completo.

---

## 9. Aproveitamento de grip

“Aproveitamento de grip” é um indicador derivado, não um canal universal.

### 9.1 Friction circle

\[
G_{resultante}=\sqrt{G_x^2+G_y^2}
\]

Uma normalização possível é:

\[
U_{grip}=\frac{G_{resultante,observado}}{G_{resultante,referência\ ou\ limite}}
\]

O denominador deve ser explicitado. Pode ser:

- limite do pneu estimado;
- máximo observado naquele pneu e sessão;
- referência de um piloto mais rápido;
- envelope histórico do carro;
- limite de um modelo de pneu.

Cada opção produz um significado diferente.

### 9.2 Métricas por curva

- pico de \(G_x\);
- pico de \(G_y\);
- aceleração resultante sustentada;
- área sob \(G_{resultante}\);
- tempo acima de um limiar de aceleração lateral;
- velocidade mínima;
- tempo de frenagem;
- tempo de aceleração;
- relação entre aceleração lateral e longitudinal;
- margem até o envelope de aderência.

O pico isolado é frágil porque pode ser provocado por zebra, ruído, erro de IMU ou evento transitório. Uma métrica sustentada e contextualizada é mais útil.

### 9.3 Interpretação

O piloto pode não estar usando o grip porque:

- freia cedo demais;
- não combina frenagem e curva de modo eficiente;
- libera o freio de forma abrupta;
- espera demais para acelerar;
- usa uma linha que reduz o raio efetivo;
- causa wheelspin;
- gera correções de direção;
- está limitado pelo pneu ou pelo setup, não pela técnica.

O score não deve atribuir automaticamente a causa ao piloto.

---

## 10. Qualidade de frenagem

### 10.1 Eventos

Uma zona de frenagem pode ser segmentada em:

1. lift-off;
2. aplicação inicial;
3. subida até o pico;
4. pico de pressão ou desaceleração;
5. modulação;
6. turn-in;
7. trail braking;
8. soltura final;
9. apex;
10. início do throttle.

### 10.2 Métricas

- ponto inicial de frenagem;
- distância de frenagem;
- duração;
- velocidade inicial;
- velocidade final;
- desaceleração média;
- desaceleração máxima;
- tempo para atingir 90% do pico;
- pressão residual no turn-in;
- pressão no apex;
- suavidade de aplicação;
- suavidade de soltura;
- número de oscilações;
- variação do brake point entre voltas;
- lock-up;
- ativação de ABS;
- velocidade de entrada;
- velocidade no apex;
- tempo até a retomada do acelerador.

### 10.3 Jerk

Com aceleração longitudinal:

\[
J(t)=\frac{da_x}{dt}
\]

Com pressão de freio:

\[
J_p(t)=\frac{dP_{brake}}{dt}
\]

A derivada precisa ser filtrada e sua taxa de amostragem deve ser considerada. Sem isso, ruído pode ser interpretado como agressividade do piloto.

### 10.4 Score de qualidade

Não existe um score universal de “qualidade da frenagem”. Uma proposta de score configurável pode combinar:

- proximidade do brake point de uma referência;
- desaceleração útil;
- baixa variabilidade;
- soltura progressiva;
- ausência de lock-up;
- velocidade de entrada adequada;
- ganho de tempo na saída.

A frenagem mais tardia não é necessariamente melhor. Se ela produzir baixa velocidade de entrada, correção excessiva ou má saída, o resultado pode ser pior.

Materiais técnicos de análise de frenagem incluem esforço, agressividade, suavidade da soltura, consistência do ponto e distância de frenagem. [web:4][web:5]

---

## 11. Métricas de curva

Para cada curva, a estrutura mínima pode ser:

- início da frenagem;
- fim da frenagem;
- turn-in;
- apex;
- throttle pickup;
- saída da curva;
- velocidade de entrada;
- velocidade mínima;
- velocidade de saída;
- tempo na curva;
- tempo perdido contra referência;
- distância percorrida;
- linha;
- raio estimado;
- aceleração lateral;
- frenagem residual;
- abertura do acelerador.

### 11.1 Saída a distância fixa

A velocidade mínima sozinha não mede bem a qualidade da saída. Uma alternativa é comparar tempo ou velocidade após uma distância fixa:

\[
\Delta t_{exit}(d)=t_{piloto}(d)-t_{referência}(d)
\]

Valores de \(d\) de 20, 50 e 100 m são úteis para diferentes categorias e curvas.

---

# Parte III, Interface e hierarquia

## 12. Hierarquia geral recomendada

A hierarquia universal de produto não precisa ser rígida. A proposta mais abrangente é:

```text
Programa / campeonato
└── Temporada
    └── Evento / etapa
        └── Dia de teste ou track day
            └── Sessão / bateria / run / stint
                └── Volta
                    └── Setor
                        └── Micro-setor
                            └── Curva / evento
                                └── Canal / métrica
```

Nem todo nível precisa existir. Um track day pode começar em “evento”; um simulador pode começar em “carro + pista + sessão”; uma equipe pode começar em “teste + run”.

### 12.1 Objeto “evento”

Um evento deve representar algo maior que uma sessão:

- campeonato;
- etapa;
- teste privado;
- track day;
- corrida online;
- temporada de simulação;
- comparação histórica.

### 12.2 Objeto “sessão/run”

Uma sessão deve conter:

- horário planejado e real;
- piloto;
- carro/moto/kart;
- objetivo;
- pneus;
- combustível;
- setup;
- condições;
- número de voltas;
- mudanças durante o run;
- resultado;
- comentários.

### 12.3 Objeto “volta”

Uma volta deve conter:

- tempo;
- validade;
- setores;
- micro-setores;
- referência usada;
- qualidade de dado;
- tráfego;
- flags;
- canal availability;
- condições;
- setup revision;
- tire state.

---

## 13. Ferramentas de referência

### 13.1 MoTeC i2

**Hierarquia prática:** arquivo/log → outing ou sessão → volta/beacon → canal/workbook.

**Visão principal:** análise de engenharia altamente configurável, com gráficos, mapas, sobreposição e cálculos.

O i2 trabalha com canais, ranges, voltas, beacons e detalhes do log. O beacon é usado para determinar voltas, gerar mapas e permitir sobreposição. [web:16][web:92]

**O que aproveitar:**

- workbook como camada de engenharia;
- canais derivados configuráveis;
- análise por volta e beacon;
- possibilidade de múltiplas referências;
- separação entre banco de dados e apresentação.

**O que não assumir:**

- que “campeonato” seja necessariamente o nível superior;
- que todos os usuários desejem a mesma tela;
- que um workbook fixo sirva para kart, moto, GT3 e fórmula.

### 13.2 AiM Race Studio 3

**Hierarquia prática:** database → eventos agrupados → sessão → voltas → canais/comentários.

**Visão principal:** banco de dados e seleção de voltas para análise.

A documentação descreve lista de canais, lista de voltas e análise de voltas provenientes de uma ou mais sessões. A ferramenta também permite selecionar os melhores N laps, primeiros N, últimos N e melhores splits para diferentes objetivos. [web:17][web:24][web:91]

O ecossistema AiM também possui referência preditiva baseada na melhor volta da sessão, melhor volta do dia, volta anterior ou volta salva da análise. [web:94]

**O que aproveitar:**

- seleção semântica de conjuntos de voltas;
- referência preditiva;
- banco de sessões;
- associação entre sessão, volta e canal.

### 13.3 Cosworth Pi Toolbox

**Hierarquia prática:** evento/teste → outing → volta → workbook/display.

**Visão principal:** aquisição e análise de pista orientada a workbooks e displays.

A terminologia pode variar conforme produto e versão. “Outing” é funcionalmente próximo de uma sessão de pista. Deve-se confirmar os detalhes de cada versão diretamente na documentação do produto.

**O que aproveitar:**

- separação entre aquisição e workbook;
- telas específicas para piloto, pneus, veículo e engenharia;
- organização por outing e volta;
- rastreamento de runs.

### 13.4 Garage61

**Hierarquia prática:** piloto/equipe → carro/pista/sessão → volta → comparação.

**Visão principal:** encontrar, selecionar e comparar voltas.

O Garage61 distingue:

- **best lap:** volta contínua mais rápida;
- **optimal lap:** combinação dos setores mais rápidos;
- ghost lap associado à telemetria;
- referência própria, de companheiro ou da base pública.

A documentação informa que ghost laps podem ser obtidos em tabelas de recordes, no analisador de voltas e em páginas de evento; também podem ser adicionados a uma coleção pessoal ou de equipe. [web:89]

**O que aproveitar:**

- comparação orientada a referência;
- best versus optimal lap;
- coleção compartilhada de referências;
- relação entre ghost e telemetria.

### 13.5 VRS

**Hierarquia prática:** série/carro/pista → sessão → volta do piloto → datapack/referência.

**Visão principal:** coaching e identificação de oportunidades.

A interface normalmente é centrada em comparação com uma volta ou datapack de referência, destacando velocidade, frenagem, acelerador, linha, setores e vídeo.

**O que aproveitar:**

- linguagem de coaching;
- comparação por oportunidade;
- referência de piloto mais rápido;
- associação entre telemetria e vídeo.

### 13.6 RaceLab

**Hierarquia prática:** carro/pista/sessão de sim → volta atual → volta de referência.

**Visão principal:** overlay em tempo real e comparação de inputs.

O RaceLab não deve ser tratado como um gerenciador completo de campeonato, teste e run sheet. Seu foco é auxiliar a condução durante a sessão, comparando inputs e referência. [web:52]

---

# Parte IV, Run sheet

## 14. O que é uma run sheet de motorsport

Em uma equipe, a run sheet é um documento operacional para executar, registrar e revisar uma tomada de dados. Ela não é apenas uma agenda. Deve conectar:

- intenção;
- configuração;
- responsável;
- execução;
- resultado;
- decisão seguinte.

Não existe um formato universal publicado para todas as categorias. O formato é uma prática de equipe e deve ser adaptado ao objetivo do teste.

### 14.1 Diferença para um setup sheet

- **Run sheet:** o que será feito, quando, por quem e com qual objetivo.
- **Setup sheet:** como o veículo está configurado.
- **Post-run report:** o que aconteceu e qual decisão foi tomada.

Em equipes pequenas, os três podem estar em uma única planilha. Em equipes maiores, são documentos relacionados.

---

## 15. Campos preenchidos antes da bateria

### Identificação

- evento;
- pista e configuração;
- data;
- horário previsto;
- sessão/run number;
- veículo;
- piloto;
- engenheiro;
- mecânico responsável;
- objetivo do run;
- prioridade do objetivo.

### Condições esperadas

- temperatura do ar;
- temperatura de pista;
- umidade;
- vento;
- pressão atmosférica;
- condição seca/molhada;
- previsão de aderência;
- horário de saída;
- posição esperada do sol, se relevante.

### Veículo e setup

- setup revision;
- combustível inicial;
- massa estimada;
- pneus, composto e jogo;
- ciclos de pneu;
- pressão fria alvo;
- temperatura alvo;
- cambagem;
- cáster;
- toe;
- barras;
- molas;
- amortecedores;
- ride height;
- asa/aero;
- diferencial;
- brake bias;
- ABS;
- TC;
- engine map;
- gear map;
- controle de tração;
- alinhamento;
- pesos de canto.

Templates públicos de setup sheet registram campos desse tipo, incluindo pista, sessão, clima, combustível, alturas, barras, molas, amortecedores, cambagem, cáster, toe, pneus, pressões, temperaturas e pesos. [web:42][web:88]

### Instrumentação

- logger;
- frequência de amostragem;
- canais esperados;
- sensores instalados;
- câmera;
- GPS;
- beacon;
- sincronização;
- cartão/memória;
- bateria;
- checklist de gravação;
- versão do arquivo de configuração.

### Plano de execução

- out-lap;
- número de voltas de aquecimento;
- voltas push;
- voltas de cooldown;
- sequência de pneus;
- sequência de combustível;
- comparação A/B;
- trecho específico da pista;
- pit-in;
- critério de interrupção;
- critério de sucesso.

---

## 16. Campos preenchidos depois da bateria

### Execução real

- horário efetivo;
- número de voltas;
- combustível inicial e final;
- pneu usado;
- temperatura real;
- condição real da pista;
- tráfego;
- bandeiras;
- incidentes;
- mudança feita no meio da sessão.

### Resultado de telemetria

- melhor volta;
- melhores setores;
- theoretical lap;
- sustainable pace;
- consistência;
- voltas válidas;
- voltas excluídas;
- motivo das exclusões;
- delta por setor;
- temperatura dos pneus;
- pressão quente;
- temperatura de freio;
- combustível por volta;
- alarmes;
- sensores inválidos;
- qualidade do GPS.

### Feedback do piloto

- entrada de curva;
- meio de curva;
- saída;
- confiança;
- equilíbrio;
- understeer;
- oversteer;
- tração;
- frenagem;
- zebra;
- vibração;
- estabilidade;
- fadiga;
- preferência subjetiva;
- comparação com o run anterior.

### Decisão

- aceitar configuração;
- rejeitar configuração;
- manter como variante;
- repetir teste;
- alterar pneu;
- alterar setup;
- alterar técnica do piloto;
- investigar sensor;
- salvar como baseline;
- criar setup target.

### Rastreabilidade

- nome do arquivo de telemetria;
- hash ou identificador do arquivo;
- setup file;
- setup sheet;
- versão de firmware;
- versão de software;
- responsável pela análise;
- link para relatório;
- data de fechamento do run.

---

## 17. Modelo de tabela de run sheet

| Campo | Antes do run | Depois do run |
|---|---|---|
| Objetivo | hipótese e prioridade | atingido, parcial ou não atingido |
| Setup | configuração planejada | configuração real e alterações |
| Pneus | composto, jogo, pressão fria | pressão quente, temperatura e desgaste |
| Combustível | massa/volume inicial | massa final, consumo e correção |
| Condições | previsão | condição efetiva |
| Piloto | instrução e foco | feedback e pontos observados |
| Telemetria | canais e logger esperados | qualidade, falhas e métricas |
| Ritmo | alvo de lap/sector | melhor, média, dispersão e potencial |
| Execução | plano de voltas | voltas realizadas e inválidas |
| Decisão | critério de aprovação | próxima ação |

---

# Parte V, Setup base e setup alvo

## 18. Setup base

O setup base é uma configuração conhecida, reproduzível e segura, usada como ponto de referência.

Deve conter:

- identificador e revisão;
- pista e configuração;
- faixa de temperatura;
- faixa de combustível;
- pneu e ciclo;
- condições de pista;
- objetivo de comportamento;
- limitações conhecidas;
- resultados históricos;
- feedback dos pilotos;
- arquivo de setup;
- setup sheet;
- data de validação.

“Base” não significa necessariamente “mais rápido”. Significa que a equipe conhece seu comportamento e consegue reproduzi-lo.

## 19. Setup alvo

O setup alvo é uma hipótese de configuração destinada a produzir um resultado específico:

- mais rotação na entrada;
- melhor tração na saída;
- menor temperatura interna do pneu;
- frenagem mais estável;
- maior velocidade mínima;
- menor arrasto;
- proteção de pneu em stint longo;
- maior janela de operação;
- menor sensibilidade a combustível;
- melhor comportamento para determinado piloto.

## 20. Origem do setup alvo

### 20.1 Histórico

Usa dados de:

- mesma pista;
- mesma categoria;
- mesmo pneu;
- mesma faixa de temperatura;
- configuração aerodinâmica semelhante;
- piloto com estilo semelhante.

### 20.2 Empírico

É obtido por mudança controlada:

1. registrar baseline;
2. mudar uma variável ou um pequeno grupo coerente;
3. repetir em condição comparável;
4. medir resposta;
5. aceitar, rejeitar ou investigar.

### 20.3 Simulação

Pode usar:

- modelo de veículo;
- modelo de pneu;
- lap-time simulation;
- otimização de suspensão;
- análise aero;
- MPC ou controle de dinâmica, quando aplicável;
- modelo de desgaste;
- modelo de temperatura.

A simulação indica sensibilidade e direção de mudança, mas depende da qualidade do modelo.

### 20.4 Híbrido

O processo mais defensável para uma equipe é:

1. histórico identifica uma região plausível;
2. simulação estima sensitividades;
3. teste físico mede resposta;
4. telemetria e feedback recalibram o modelo;
5. setup validado vira nova referência.

A literatura recente sobre otimização de GT3 trata a otimização como condicionada ao setup e à telemetria, não como uma busca abstrata independente da configuração utilizada. [web:33]

## 21. Baseline, target e resultado

O modelo de dados deve manter três objetos diferentes:

```text
BASE-2026.08
└── TARGET-2026.08-A
    ├── hipótese
    ├── mudanças
    ├── condições-alvo
    ├── resultado de telemetria
    ├── feedback do piloto
    └── decisão
```

A decisão pode ser:

- `accepted_as_new_base`;
- `accepted_as_variant`;
- `rejected`;
- `inconclusive`;
- `repeat_required`;
- `sensor_issue`;
- `driver_limited`;
- `condition_limited`.

O setup ideal não é obrigatoriamente o setup que gera a volta única mais rápida. Para track day e corrida, muitas vezes é o setup que maximiza ritmo repetível, janela operacional e confiança do piloto.

---

# Parte VI, Moto e kart

## 22. Moto: canais principais

### 22.1 Canais

- GPS;
- velocidade;
- RPM;
- marcha;
- throttle;
- brake pressure dianteiro;
- brake pressure traseiro;
- wheel speed dianteira;
- wheel speed traseira;
- slip ratio;
- lean angle;
- roll rate;
- yaw rate;
- pitch rate;
- aceleração longitudinal;
- aceleração lateral;
- suspensão dianteira;
- suspensão traseira;
- quickshifter;
- temperatura e pressão de pneu;
- temperatura de motor.

Nem toda moto possui todos os canais. A disponibilidade deve ser parte do perfil do veículo.

### 22.2 KPIs

- ângulo de inclinação máximo;
- velocidade no ângulo máximo;
- taxa de entrada em inclinação;
- taxa de recuperação;
- tempo em determinada faixa de inclinação;
- brake release versus lean angle;
- throttle pickup versus lean angle;
- wheel speed delta;
- wheelspin;
- velocidade de entrada, apex e saída;
- tempo de curva;
- trajetória;
- pitch durante frenagem;
- transferência de carga;
- uso de suspensão;
- consistência da linha.

A maior inclinação não é automaticamente melhor. Ela deve ser contextualizada com velocidade, raio, aceleração lateral, throttle e tempo de curva.

Materiais de análise de moto destacam velocidade, inclinação, throttle e frenagem como canais centrais. Dashboards de moto também oferecem GPS, velocidade, intermediários e canais relacionados à dinâmica. [web:37][web:39]

### 22.3 Ausência de pressão de freio

Se não houver sensor de pressão, é possível estimar frenagem por:

- derivada da velocidade;
- aceleração longitudinal;
- estado do throttle;
- pitch;
- wheel speed.

Essa variável deve ser marcada como `proxy_brake`, nunca como pressão real.

### 22.4 Hang-off

Se houver câmera, IMU ou sensor de posição, pode-se investigar:

- posição do piloto;
- timing do movimento;
- relação entre hang-off e lean angle;
- estabilidade durante frenagem;
- custo de transição entre curvas.

Sem medição, não se deve inferir com confiança a posição corporal apenas da telemetria de veículo.

---

## 23. Kart: canais principais

### 23.1 Canais que podem faltar

- suspensão convencional;
- amortecedores;
- ride height instrumentado;
- diferencial tradicional;
- steering angle;
- pressão de freio contínua;
- wheel speed individual.

### 23.2 Canais úteis

- GPS;
- velocidade;
- trajetória;
- RPM;
- throttle;
- brake position ou pressão;
- aceleração longitudinal;
- aceleração lateral;
- yaw rate;
- steering angle, se instalado;
- wheel speed, se instalado;
- temperatura de água;
- EGT;
- temperatura de pneu;
- pressão de pneu;
- tempo de lift-off;
- retorno ao acelerador.

### 23.3 KPIs de kart

- velocidade mínima;
- velocidade de saída;
- tempo até o throttle;
- tempo de lift;
- tempo de coasting;
- perda por correção;
- consistência de trajetória;
- yaw rate;
- rotação da roda interna, se disponível;
- wheel lift ou proxy de rotação;
- temperatura de pneu;
- comportamento de motor.

Na ausência de steering angle, use linha GPS, yaw rate e aceleração lateral. Não chame “suavidade do volante” uma métrica derivada da trajetória; rotule-a como suavidade de trajetória ou de yaw.

Materiais técnicos de kart destacam velocidade, direção e acelerador como canais básicos para interpretação do desempenho. [web:45]

---

# Parte VII, Modelo de produto

## 24. Perfis de interface

### 24.1 Piloto amador

Mostrar:

- melhor volta;
- ritmo sustentável;
- consistência;
- delta por curva;
- uma recomendação;
- vídeo/linha;
- comparação simples de frenagem e saída.

### 24.2 Piloto avançado

Adicionar:

- sobreposição de canais;
- theoretical lap;
- repeatability gap;
- brake release;
- throttle pickup;
- trajetória;
- comparação por condição;
- análise de curva.

### 24.3 Engenheiro

Adicionar:

- workbooks;
- canais brutos;
- canais derivados;
- qualidade de aquisição;
- setup e run sheet;
- pneus e combustível;
- histórico de testes;
- correlação entre alteração e resultado;
- análise de confiabilidade.

---

## 25. Metadados e rastreabilidade

Cada resultado deve ser reproduzível. O sistema deve registrar:

- fonte do dado: AiM, MoTeC, Bosch, Pi/Cosworth, sim;
- arquivo original;
- parser e versão;
- canal original;
- unidade original;
- conversão aplicada;
- filtro aplicado;
- algoritmo de detecção de volta;
- mapa da pista;
- versão do setor/micro-setor;
- referência usada;
- exclusões;
- setup revision;
- condições;
- usuário que aprovou a análise.

Sem isso, uma alteração no algoritmo pode fazer a mesma sessão produzir resultados diferentes sem explicação.

---

## 26. Contrato de cada métrica

Cada KPI pode possuir um registro como:

```yaml
metric_id: brake_quality_score
name: Brake quality score
category: interpreted
status: heuristic_score
inputs:
  - brake_pressure
  - longitudinal_acceleration
  - speed
  - yaw_rate
reference_required: true
valid_for:
  - car
not_valid_without:
  - brake_pressure
proxy_allowed: true
formula_version: 1.0.0
explanation: >-
  Score configurável baseado em consistência do ponto de frenagem,
  desaceleração útil, suavidade da soltura e velocidade de entrada.
```

Isso permite que o usuário saiba se a métrica foi medida, calculada ou interpretada.

---

## 27. Recomendação de implementação

### Fase 1, fundamentos

- normalização de canais;
- unidades;
- GPS e distância na pista;
- detecção de voltas;
- setores e micro-setores;
- delta;
- validade;
- best/optimal/theoretical lap;
- comparação de sessões.

### Fase 2, driver analysis

- detecção de frenagem;
- brake point;
- throttle pickup;
- velocidade mínima e saída;
- coasting;
- consistência;
- repeatability gap;
- recomendações por curva.

### Fase 3, vehicle engineering

- pneus;
- combustível;
- suspensão;
- freios;
- motor;
- qualidade do sinal;
- setup revision;
- run sheet.

### Fase 4, progressão e histórico

- eventos e etapas;
- comparação longitudinal;
- baseline/target;
- histórico de mudanças;
- correlação entre setup e resultado;
- relatórios de evolução.

### Fase 5, perfis por veículo

- carro;
- moto;
- kart;
- fórmula;
- protótipo;
- simulação.

---

## 28. Conclusões refinadas

1. **Os KPIs realmente úteis são contextuais.** O mesmo tempo de volta pode resultar de melhor frenagem, melhor saída, pneu novo, menor combustível ou tráfego.
2. **A melhor volta não basta.** Melhor volta, theoretical lap, ritmo sustentável e consistência devem ser exibidos separadamente.
3. **Scores precisam ser transparentes.** “Qualidade de frenagem” e “aproveitamento de grip” são úteis como índices, mas não são padrões universais.
4. **Run sheet é prática operacional.** Não há formato universal; o núcleo é objetivo, configuração, responsável, execução, resultado e decisão.
5. **Setup base é referência, não necessariamente o mais rápido.** Setup alvo é uma hipótese que pode vir de histórico, teste, simulação ou combinação dos três.
6. **Simulação e histórico são complementares.** Simulação oferece sensitividade e direção; dados reais oferecem correlação, pneus, irregularidades, piloto e confiabilidade.
7. **Moto e kart exigem modelos próprios.** Não basta remover canais de carro; a lógica de dinâmica, sensores e interpretação muda.
8. **A hierarquia deve ser flexível.** Campeonato, etapa, sessão e volta são níveis úteis, mas nem sempre todos existem.
9. **A procedência do KPI é parte do produto.** O usuário deve saber o que foi medido, derivado, inferido ou interpretado.
10. **A interface deve terminar em uma ação.** A análise ideal não apenas mostra onde o tempo foi perdido; sugere o que testar na próxima sessão e registra o resultado.

---

# Referências consultadas

- [web:1] Track Day Analysis, progressão, melhor volta, consistência, grip, coasting e desempenho por curva.
- [web:2] Braking Lab, zonas de frenagem, pressão máxima, trail braking e comparação de voltas.
- [web:3] Virtual Racing School, metas de prática, braking points, consistência, apex speed, exit speed e linha.
- [web:4] Referência de análise de frenagem, esforço, agressividade, suavidade, consistência e distância.
- [web:5] HPDE Logbook, threshold braking, late braking, trail braking, brake point consistency e smooth release.
- [web:13] Braking Lab, análise de zonas de frenagem e métricas de pressão.
- [web:16] MoTeC i2, logs, canais, ranges, voltas, beacons e detalhes.
- [web:17] AiM Race Studio 3, canais e voltas na análise.
- [web:24] AiM Race Studio, agrupamento de sessões em eventos no banco de dados.
- [web:25] Cosworth, user guides and manuals.
- [web:26] Cosworth Pi Toolbox, materiais de análise e integração com iRacing.
- [web:33] Pesquisa sobre otimização de setup condicionada por telemetria.
- [web:36] Race Team Run Sheet, exemplo público de campos operacionais e condições.
- [web:37] Apexingest, canais e análise de telemetria de moto.
- [web:39] Starlane, exemplo de canais disponíveis em dashboard de moto.
- [web:40] Motorsport telemetry, distinção entre dados e interpretação de telemetria.
- [web:42] HP Academy, exemplo de setup sheet de motorsport.
- [web:45] TKART, leitura de dados de telemetria de kart.
- [web:51] Garage61, documentação geral de uso.
- [web:52] RaceLab, overlay de inputs e comparação de voltas.
- [web:53] Garage61 Pro, voltas, telemetria, ghost laps e setups.
- [web:58] VRS, video analyzer e comparação com datapack.
- [web:76] PLOS ONE, comparação de comportamento humano e autônomo em simulador profissional.
- [web:78] Scitepress, métricas de sim racing e otimização de performance.
- [web:80] F1 data visualization, lap differential, consistência e perfis normalizados de velocidade.
- [web:88] Cal Poly Racing / FSAE, exemplo de template de teste e setup.
- [web:89] Garage61, ghost laps, best laps, optimal laps e telemetria associada.
- [web:90] AiM Race Studio 3, documentação geral.
- [web:91] AiM Race Studio 3, seleção de melhores, primeiras, últimas e melhores voltas por split.
- [web:92] MoTeC, beacon, canais necessários e geração de voltas/mapas.
- [web:94] AiM, predictive reference lap e referências salvas.

> **Status das referências:** as fontes de software sustentam funções e organização declaradas pelos produtos. Templates e materiais de equipes sustentam campos recorrentes. As fórmulas, a classificação de métricas e a arquitetura de produto deste documento são recomendações de engenharia, não padrões oficiais de uma federação.