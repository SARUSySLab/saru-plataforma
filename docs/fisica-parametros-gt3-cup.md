# Proveniência dos parâmetros do 911 GT3 Cup

Auditoria de 2026-09-13 sobre `src/saru_poc/fisica/parametros_gt3_cup.py`, feita quando o
módulo veio do repositório `saru` para a PoC. Nenhum valor foi alterado. O que este arquivo
acrescenta é a conferência de cada número contra a fonte que o módulo diz ter usado.

## Como ler

Três coisas foram comparadas, nesta ordem.

1. O que o módulo declara, na docstring do módulo e na docstring de cada preset.
2. O que a pesquisa externa já validou link a link, em `_auditoria/07-pesquisa-simulacao.md`,
   seção 6, com os comunicados oficiais da Porsche e a imprensa especializada.
3. O preset antigo `porsche_911_gt3_cup_991()`, em
   `_arquivo/saru-physics-py/src/saru_core/vehicle/parameters.py`, linha 643, que tratava
   991.1 e 991.2 como um carro só.

Vocabulário de status:

- confirmado: fonte oficial da Porsche ou do fornecedor diz o mesmo número.
- só imprensa: o número aparece em veículo especializado, sem comunicado oficial localizado.
- estimativa de engenharia: ninguém publicou o valor, ele foi arbitrado para o modelo rodar.
- divergente do preset antigo: o valor mudou em relação ao preset de 2021, sem nota do porquê.
- divergente da fonte: o valor contradiz o que a fonte citada diz.
- não encontrado: nenhuma das três comparações alcança o valor.
- a confirmar com Vitor: só o manual técnico, que Vitor tem, resolve.

## Achado que vale antes das tabelas

O módulo tem a classe `ParameterValue` e o enum `Provenance`, com os quatro níveis
`MANUAL_OFICIAL`, `HOMOLOGACAO_REGULAMENTO`, `FORNECEDOR_TECNICO` e
`ESTIMATIVA_ENGENHARIA`. Nenhum dos dois é usado em lugar algum do arquivo. Nenhum valor
numérico carrega proveniência própria. O que existe é a lista de seis fontes na docstring do
módulo e uma frase por preset dizendo "especificação homologada".

Consequência prática: a coluna "proveniência declarada" abaixo não pôde ser lida do código
valor a valor. Ela foi reconstruída a partir de qual das seis fontes cobre aquele assunto.
Enquanto `ParameterValue` não for usado, nenhum valor deste módulo é rastreável sozinho. A decisão
entre usar as duas definições ou removê-las está na issue #19 da PoC, ligada a PIL-RF-29 e ao
critério PIL-CT-47.

## 991.1, motor 3.8 L, 2013 a 2016

Fonte externa disponível para esta geração: só imprensa especializada. A pesquisa não achou
o comunicado oficial de 2013.

| Parâmetro | Valor | Unidade | Proveniência declarada no código | Fonte que confirma | Status |
|---|---|---|---|---|---|
| Massa base | 1175 | kg | Manual Técnico 991 Fase 1 e 2 | motorauthority, stuttcars, racecarsforyou | só imprensa |
| Massa de corrida | 1255 | kg | Manual Técnico 991 Fase 1 e 2 | nenhuma; preset antigo usa 1250 | divergente do preset antigo |
| Entre-eixos | 2,463 | m | Manual Técnico 991 Fase 1 e 2 | imprensa especializada, 2.463 mm | só imprensa |
| Bitola dianteira e traseira | 1,545 e 1,530 | m | Manual Técnico 991 Fase 1 e 2 | nenhuma; igual ao preset antigo (média 1,537) | não encontrado |
| lf e lr | 1,034 e 1,429 | m | Manual Técnico 991 Fase 1 e 2 | nenhuma; preset antigo usa 1,08 e 1,38 | divergente da fonte, ver seção de incoerências |
| Altura do CG | 0,450 | m | não declarada | nenhuma; preset antigo usa 0,46 | divergente do preset antigo |
| Iz, Ix, Iy | 1500, 320, 1600 | kg·m² | não declarada | preset antigo, mesmos três valores | estimativa de engenharia |
| Relação de direção | 14,5 | adimensional | não declarada | nenhuma | não encontrado |
| Distribuição de peso dianteira | 42,0 | % | não declarada | a Porsche não publica em nenhuma geração | estimativa de engenharia |
| Potência máxima | 338 (460) | kW (cv) a 7500 rpm | Manual Técnico 991 Fase 1 e 2 | imprensa especializada; igual ao preset antigo | só imprensa |
| Torque máximo | 440 | N·m a 6250 rpm | Manual Técnico 991 Fase 1 e 2 | preset antigo, mesmo valor; sem fonte pública na pesquisa | só imprensa |
| Cilindrada | 3797 | cm³ | Manual Técnico 991 Fase 1 e 2 | imprensa fala em boxer 3,8 L, sem o número exato | só imprensa |
| Corte e limite de giro | 8500 e 9000 | rpm | Manual Técnico 991 Fase 1 e 2 | preset antigo, mesmos dois valores | estimativa de engenharia |
| Curva de torque, 10 pontos | 200 a 440 | N·m | não declarada | preset antigo tem 11 pontos e valores diferentes | divergente do preset antigo |
| Temperaturas máximas de óleo e água | 140 e 110 | °C | Porsche Channels Manual | preset antigo, mesmos dois valores | estimativa de engenharia |
| Pressões mínimas de óleo, água e combustível | 5,5, 0,5 e 4,5 | bar | Porsche Channels Manual | nenhuma | a confirmar com Vitor |
| Pneu dianteiro e traseiro | 245/640-18 e 305/660-18 | polegada | Michelin Customer Racing Guide | a pesquisa 07 registra 27/65-18 e 31/71-18 para o 991.1; o preset antigo registra 245/650-18 | divergente da fonte |
| Aro dianteiro e traseiro | 9.5J x 18 e 12.0J x 18 | polegada | Michelin Customer Racing Guide | nenhuma | não encontrado |
| Pressão a frio e alvo a quente | 1,40 e 2,00 | bar | Michelin Customer Racing Guide | preset antigo usa 1,7 bar a frio | divergente do preset antigo |
| Temperatura ótima de pneu | 90 | °C | Michelin Customer Racing Guide | preset antigo, mesmo valor | estimativa de engenharia |
| Raio de rolamento dianteiro e traseiro | 0,324 e 0,338 | m | não declarada | preset antigo usa um raio só, 0,330 | divergente do preset antigo |
| Rigidez de curva dianteira e traseira | 72000 e 88000 | N/rad | não declarada | preset antigo usa 75000 e 90000 | divergente do preset antigo |
| Coeficiente de atrito | 1,52 | adimensional | não declarada | preset antigo usa 1,55 | divergente do preset antigo |
| Pacejka B, C, D, E | 21,0, 1,35, 1,52 e 0,94 | adimensional | não declarada | preset antigo usa 22,0, 1,35, 1,55 e 0,95 | divergente do preset antigo |
| Sensibilidade à carga (k) | -0,11 | 1/N | não declarada | pesquisa da KB fecha a banda -0,10 a -0,15 | estimativa de engenharia |
| Cd, área frontal e Cl | 0,385, 1,98 e -0,58 | adimensional e m² | não declarada | a Porsche não publica aerodinâmica do Cup; preset antigo usa 0,38 e -0,60 | estimativa de engenharia |
| Downforce a 200 e 250 km/h | 700 e 1090 | N | não declarada | nenhuma | estimativa de engenharia |
| Asa traseira, posições | 9 | posições | Regulamento Técnico | preset antigo cita 9 posições na docstring | só imprensa |
| Câmbio e acionamento | sequencial 6 marchas, paddle pneumático | | Manual Técnico 991 Fase 1 e 2 | imprensa confirma sequencial dog-type de 6 marchas por paletas | só imprensa |
| Relações de marcha e diferencial | 3,167 a 1,029 e 3,444 | adimensional | não declarada | preset antigo usa 3,091 na primeira, igual nas outras cinco e no diferencial | divergente do preset antigo |
| Eficiência e tempo de troca | 0,97 e 0,060 | adimensional e s | não declarada | preset antigo usa 0,97 e 0,05 s | divergente do preset antigo |
| Disco dianteiro e traseiro | 380 x 32 e 380 x 30 | mm | Manual Técnico 991 Fase 1 e 2 | preset antigo, mesma ficha na docstring | a confirmar com Vitor |
| Pinças, pistões dianteiros e traseiros | 6 e 4 | pistões | Manual Técnico 991 Fase 1 e 2 | preset antigo, mesma ficha | a confirmar com Vitor |
| Pastilha e atrito | Pagid RSL29 e 0,42 | adimensional | PAGID Racing Technical Specifications | o fact-check do GT3 R confirma RSL29 com atrito de 0,41 a 0,44, em fonte do fabricante, para o GT3 R e não para o Cup | confirmado para o composto, a confirmar para o carro |
| Balanço de freio e faixa | 58,0 e 52,0 a 66,0 | % | não declarada | preset antigo usa 58,0 sem faixa | estimativa de engenharia |
| ABS e controle de tração | ausentes | | Regulamento Técnico | preset antigo liga ABS para o 991 inteiro | divergente do preset antigo |

## 991.2, motor 4.0 L, 2017 a 2020

Fonte externa disponível: comunicado oficial Porsche Newsroom 13026 e o media guide da
Porsche Cars North America. É a geração com a melhor cobertura oficial das três.

| Parâmetro | Valor | Unidade | Proveniência declarada no código | Fonte que confirma | Status |
|---|---|---|---|---|---|
| Massa base | 1200 | kg | Manual Técnico 991 Fase 1 e 2 | Newsroom 13026, que chama 1.200 kg de pronto para corrida | confirmado, com o rótulo trocado |
| Massa de corrida | 1280 | kg | Manual Técnico 991 Fase 1 e 2 | nenhuma; a fonte oficial já usa 1.200 kg como massa de corrida | divergente da fonte |
| Entre-eixos | 2,463 | m | Manual Técnico 991 Fase 1 e 2 | Newsroom 13026 publica 2.456 mm | divergente da fonte |
| Bitola dianteira e traseira | 1,545 e 1,530 | m | Manual Técnico 991 Fase 1 e 2 | nenhuma; a fonte oficial publica largura total de 1.980 mm, que é outra medida | não encontrado |
| lf e lr | 1,034 e 1,429 | m | Manual Técnico 991 Fase 1 e 2 | nenhuma | divergente da fonte, ver seção de incoerências |
| Altura do CG | 0,450 | m | não declarada | nenhuma; preset antigo usa 0,46 | divergente do preset antigo |
| Iz, Ix, Iy | 1550, 330, 1650 | kg·m² | não declarada | nenhuma; preset antigo usa 1500, 320 e 1600 | estimativa de engenharia |
| Relação de direção | 14,5 | adimensional | não declarada | nenhuma | não encontrado |
| Distribuição de peso dianteira | 42,0 | % | não declarada | a Porsche não publica em nenhuma geração | estimativa de engenharia |
| Potência máxima | 357 (485) | kW (cv) a 7500 rpm | Manual Técnico 991 Fase 1 e 2 | Newsroom 13026, mesmos três números | confirmado |
| Torque máximo | 480 | N·m a 6250 rpm | Manual Técnico 991 Fase 1 e 2 | Newsroom 13026, mesmos dois números | confirmado |
| Cilindrada | 3996 | cm³ | Manual Técnico 991 Fase 1 e 2 | Newsroom 13026 | confirmado |
| Corte e limite de giro | 8500 e 9000 | rpm | Manual Técnico 991 Fase 1 e 2 | nenhuma | a confirmar com Vitor |
| Curva de torque, 10 pontos | 220 a 480 | N·m | não declarada | nenhuma | estimativa de engenharia |
| Temperaturas máximas de óleo e água | 140 e 110 | °C | Porsche Channels Manual | preset antigo, mesmos dois valores | estimativa de engenharia |
| Pressões mínimas de óleo, água e combustível | 5,5, 0,5 e 2,5 | bar | Porsche Channels Manual | nenhuma | a confirmar com Vitor |
| Pneu dianteiro e traseiro | 270/650-18 e 310/710-18 | polegada | Michelin Customer Racing Guide | Newsroom 13026 confirma 270 mm e 310 mm em aro 18; os perfis 650 e 710 não aparecem | confirmado na largura, a confirmar no perfil |
| Aro dianteiro e traseiro | 10.5J x 18 e 12.0J x 18 | polegada | Michelin Customer Racing Guide | nenhuma | não encontrado |
| Pressão a frio e alvo a quente | 1,45 e 2,05 | bar | Michelin Customer Racing Guide | preset antigo usa 1,7 bar a frio | divergente do preset antigo |
| Temperatura ótima de pneu | 90 | °C | Michelin Customer Racing Guide | preset antigo, mesmo valor | estimativa de engenharia |
| Raio de rolamento dianteiro e traseiro | 0,329 e 0,342 | m | não declarada | preset antigo usa um raio só, 0,330 | divergente do preset antigo |
| Rigidez de curva dianteira e traseira | 76000 e 92000 | N/rad | não declarada | preset antigo usa 75000 e 90000 | divergente do preset antigo |
| Coeficiente de atrito | 1,55 | adimensional | não declarada | preset antigo, mesmo valor | estimativa de engenharia |
| Pacejka B, C, D, E | 21,5, 1,36, 1,55 e 0,93 | adimensional | não declarada | preset antigo usa 22,0, 1,35, 1,55 e 0,95 | divergente do preset antigo |
| Sensibilidade à carga (k) | -0,115 | 1/N | não declarada | pesquisa da KB fecha a banda -0,10 a -0,15 | estimativa de engenharia |
| Cd, área frontal e Cl | 0,395, 2,00 e -0,70 | adimensional e m² | não declarada | a pesquisa 07 registra que a aerodinâmica do 991.2 não é publicada numericamente | estimativa de engenharia |
| Downforce a 200 e 250 km/h | 850 e 1330 | N | não declarada | nenhuma | estimativa de engenharia |
| Asa traseira, posições e largura | 9 posições, 1.840 mm na docstring | posições e mm | Regulamento Técnico | nenhuma | não encontrado |
| Câmbio e acionamento | sequencial 6 marchas, paddle pneumático | | Manual Técnico 991 Fase 1 e 2 | Newsroom 13026 confirma sequencial de 6 marchas | confirmado no câmbio, a confirmar no acionamento |
| Relações de marcha e diferencial | 3,167 a 1,029 e 3,444 | adimensional | não declarada | idênticas às do 991.1 e às do 992.1 dentro do próprio módulo | divergente da fonte |
| Eficiência e tempo de troca | 0,97 e 0,055 | adimensional e s | não declarada | preset antigo usa 0,97 e 0,05 s | divergente do preset antigo |
| Disco dianteiro e traseiro | 380 x 32 e 380 x 30 | mm | Manual Técnico 991 Fase 1 e 2 | preset antigo, mesma ficha na docstring | a confirmar com Vitor |
| Pinças, pistões dianteiros e traseiros | 6 e 4 | pistões | Manual Técnico 991 Fase 1 e 2 | preset antigo, mesma ficha | a confirmar com Vitor |
| Pastilha e atrito | Pagid RSL29 e 0,42 | adimensional | PAGID Racing Technical Specifications | fact-check do GT3 R, não do Cup | confirmado para o composto, a confirmar para o carro |
| Balanço de freio e faixa | 58,0 e 52,0 a 66,0 | % | não declarada | preset antigo usa 58,0 sem faixa | estimativa de engenharia |
| ABS, canais, e controle de tração | presente, 10 canais, sem TC | | Regulamento Técnico | nenhuma | a confirmar com Vitor |

## 992.1, motor 4.0 L, 2021 em diante

Fonte externa disponível: comunicados oficiais Porsche Newsroom 23150 e 23202, mais
tyre-trends para a medida de pneu. Comprimento e entre-eixos só aparecem em stuttcars.

| Parâmetro | Valor | Unidade | Proveniência declarada no código | Fonte que confirma | Status |
|---|---|---|---|---|---|
| Massa base | 1260 | kg | Technical Manual 911 GT3 Cup (992) | Newsroom 23150 e 23202, mesmo valor | confirmado |
| Massa de corrida | 1340 | kg | Technical Manual 911 GT3 Cup (992) | nenhuma; a diferença de 80 kg é o piloto, arbitrada | estimativa de engenharia |
| Entre-eixos | 2,502 | m | Technical Manual 911 GT3 Cup (992) | stuttcars publica 2.459 mm, sem confirmação oficial | divergente da fonte |
| Bitola dianteira e traseira | 1,920 e 1,902 | m | Technical Manual 911 GT3 Cup (992) | os comunicados oficiais publicam 1.920 mm e 1.902 mm como largura da carroceria, não como bitola | divergente da fonte |
| lf e lr | 1,001 e 1,501 | m | Technical Manual 911 GT3 Cup (992) | nenhuma | divergente da fonte, ver seção de incoerências |
| Altura do CG | 0,440 | m | não declarada | nenhuma | estimativa de engenharia |
| Iz, Ix, Iy | 1650, 350, 1750 | kg·m² | não declarada | nenhuma | estimativa de engenharia |
| Relação de direção | 13,8 | adimensional | não declarada | nenhuma | não encontrado |
| Distribuição de peso dianteira | 40,0 | % | não declarada | a Porsche não publica em nenhuma geração | estimativa de engenharia |
| Potência máxima | 375 (510) | kW (cv) a 8400 rpm | Technical Manual 911 GT3 Cup (992) | Newsroom 23150 e 23202, mesmos três números | confirmado |
| Torque máximo | 470 | N·m a 6150 rpm | Technical Manual 911 GT3 Cup (992) | Newsroom 23150 e 23202, mesmos dois números | confirmado |
| Cilindrada | 3996 | cm³ | Technical Manual 911 GT3 Cup (992) | Newsroom 23150 e 23202 | confirmado |
| Corte de giro | 8750 | rpm | Technical Manual 911 GT3 Cup (992) | Newsroom 23150 e 23202 registram corte a 8.750 rpm | confirmado |
| Limite de segurança | 9000 | rpm | Technical Manual 911 GT3 Cup (992) | nenhuma | a confirmar com Vitor |
| Curva de torque, 10 pontos | 210 a 470 | N·m | não declarada | nenhuma | estimativa de engenharia |
| Temperaturas máximas de óleo e água | 130 e 110 | °C | Porsche Channels Manual | nenhuma | a confirmar com Vitor |
| Pressões mínimas de óleo, água e combustível | 4,0, 0,6 e 3,0 | bar | Porsche Channels Manual | nenhuma | a confirmar com Vitor |
| Pneu dianteiro e traseiro | 30/65-18 e 31/71-18 | polegada | Michelin Customer Racing Guide | Newsroom e tyre-trends confirmam Michelin Pilot Sport Cup N3 nas duas medidas | confirmado |
| Aro dianteiro e traseiro | 12.0J x 18 e 13.0J x 18 | polegada | Michelin Customer Racing Guide | nenhuma | não encontrado |
| Pressão a frio e alvo a quente | 1,45 e 2,00 | bar | Michelin Customer Racing Guide | nenhuma | a confirmar com Vitor |
| Temperatura ótima de pneu | 92 | °C | Michelin Customer Racing Guide | nenhuma | estimativa de engenharia |
| Raio de rolamento dianteiro e traseiro | 0,332 e 0,355 | m | não declarada | nenhuma | estimativa de engenharia |
| Rigidez de curva dianteira e traseira | 82000 e 98000 | N/rad | não declarada | nenhuma | estimativa de engenharia |
| Coeficiente de atrito | 1,60 | adimensional | não declarada | nenhuma | estimativa de engenharia |
| Pacejka B, C, D, E | 22,0, 1,40, 1,60 e 0,92 | adimensional | não declarada | nenhuma | estimativa de engenharia |
| Sensibilidade à carga (k) | -0,120 | 1/N | não declarada | pesquisa da KB fecha a banda -0,10 a -0,15 e converge em -0,12 | estimativa de engenharia |
| Cd, área frontal e Cl | 0,420, 2,05 e -1,05 | adimensional e m² | não declarada | a pesquisa 07 registra que nenhum coeficiente aerodinâmico do Cup é publicado | estimativa de engenharia |
| Downforce a 200 e 250 km/h | 1300 e 2030 | N | não declarada | nenhuma | estimativa de engenharia |
| Asa traseira, posições | 11 | posições | Technical Manual 911 GT3 Cup (992) | Newsroom confirma asa traseira de 11 posições | confirmado |
| Câmbio e acionamento | sequencial 6 marchas, atuador elétrico | | Technical Manual 911 GT3 Cup (992) | Newsroom confirma sequencial de 6 marchas com atuador eletrônico | confirmado |
| Relações de marcha e diferencial | 3,167 a 1,029 e 3,444 | adimensional | não declarada | idênticas às das duas gerações 991 dentro do próprio módulo | divergente da fonte |
| Eficiência e tempo de troca | 0,97 e 0,040 | adimensional e s | não declarada | nenhuma | estimativa de engenharia |
| Disco dianteiro e traseiro | 380 x 32 e 380 x 32 | mm | Technical Manual 911 GT3 Cup (992) | nenhuma | a confirmar com Vitor |
| Pinças, pistões dianteiros e traseiros | 6 e 4 | pistões | Technical Manual 911 GT3 Cup (992) | nenhuma | a confirmar com Vitor |
| Pastilha e atrito | Pagid RSL29 e 0,42 | adimensional | PAGID Racing Technical Specifications | fact-check do GT3 R, não do Cup | confirmado para o composto, a confirmar para o carro |
| Balanço de freio e faixa | 57,5 e 52,0 a 65,0 | % | não declarada | nenhuma | estimativa de engenharia |
| ABS, canais e controle de tração | presente, 10 canais, com TC | | Technical Manual 911 GT3 Cup (992) | Newsroom registra ABS e controle de tração no 992.1 | confirmado na existência, a confirmar nos 10 canais |

## Incoerências que a conferência achou

### lf e lr parecem trocados nas três gerações

O 911 tem o motor atrás do eixo traseiro, então o centro de gravidade fica perto do eixo
traseiro: lf grande, lr pequeno. O módulo faz o contrário. Nas duas gerações 991, lf vale
1,034 m e lr vale 1,429 m, com entre-eixos de 2,463 m. A carga estática no eixo dianteiro é
lr dividido pelo entre-eixos, o que dá 58,0 por cento na frente. O mesmo preset declara
42,0 por cento na frente. No 992.1, lf de 1,001 m e lr de 1,501 m dão 60,0 por cento na
frente contra os 40,0 por cento declarados.

Os 42,0 e os 40,0 batem exatamente com lf dividido pelo entre-eixos. Ou seja, quem escreveu
usou lf onde a fórmula pede lr. Trocar os dois valores deixa o módulo coerente consigo
mesmo e com o carro. O preset antigo tem o mesmo problema, com lf de 1,08 m e lr de 1,38 m,
que dão 56,0 por cento na frente.

Isso não é novidade na casa. A auditoria 08 registra que o arquivo
`vehicle_992_gt3_r.yaml` teve lf e lr corrigidos em 2026-07-15 depois de a mesma inversão
ser detectada, e que a KB avisa que o relatório de origem trocava os dois.

Nada foi alterado aqui. A correção é decisão de Vitor porque muda o comportamento de
qualquer modelo de bicicleta que use o preset.

### Bitola do 992.1 pode ser largura de carroceria

O módulo grava 1,920 m e 1,902 m como bitola dianteira e traseira do 992.1, e a docstring
repete "bitola 1.920 mm". A pesquisa 07 registra esses mesmos dois números como largura,
vindos de comunicado oficial. Duas evidências sugerem que são largura de carroceria, não
bitola. A primeira é interna: para o 991.2 a mesma pesquisa dá largura total de 1.980 mm e
o módulo grava bitola de 1,545 m, ou seja, a casa já trata largura e bitola como medidas
diferentes. A segunda é aritmética: uma bitola igual à largura total exigiria pneu com
espessura zero para fora da roda.

O teste `test_992_difere_do_991_em_entre_eixos_e_bitola` só verifica que o 992.1 tem números
próprios, sem afirmar direção nem valor, justamente porque as duas leituras seguem abertas.
Nenhum teste protege contra esse erro enquanto o manual não for aberto.

### Entre-eixos do 992.1

O módulo usa 2,502 m e a docstring do teste fala em 39 mm a mais que o 991. A única fonte
que a pesquisa 07 achou, stuttcars, publica 2.459 mm, que é 4 mm a menos que o 991.1, não
39 a mais. A Porsche não publicou o valor. É a divergência mais fácil de fechar com o
manual técnico.

### Massa de corrida do 991.2

O comunicado oficial 13026 chama 1.200 kg de massa pronta para corrida. O módulo usa esse
mesmo 1.200 kg como massa base e cria 1.280 kg como massa de corrida. Ou a fonte oficial
fala de massa seca e o rótulo dela está errado, ou o módulo somou piloto duas vezes.

### Relações de marcha iguais nas três gerações

As seis relações e o diferencial são idênticos em 991.1, 991.2 e 992.1. O 992.1 trocou o
câmbio inteiro, do acionamento pneumático para o elétrico. A chance de as seis relações
terem ficado iguais é baixa. O preset antigo, para o 991, usava 3,091 na primeira em vez de
3,167, o que reforça que o número atual não veio de ficha.

### Pneu do 991.1

O módulo usa 245/640-18 e 305/660-18. A pesquisa 07 registra 27/65-18 e 31/71-18 para o
991.1, em notação Michelin de polegada. O preset antigo registra 245/650-18 e 305/660-18.
Três fontes, três respostas para o dianteiro.

## Resumo por status

Contagem sobre as 109 linhas das três tabelas: 36 no 991.1, 36 no 991.2 e 37 no 992.1.

| Status | Linhas |
|---|---|
| confirmado em fonte oficial ou de fornecedor | 11 |
| confirmado em parte, com ressalva na própria linha | 7 |
| só imprensa | 7 |
| estimativa de engenharia | 34 |
| divergente do preset antigo | 17 |
| divergente da fonte citada | 10 |
| não encontrado | 9 |
| a confirmar com Vitor | 14 |

Dezoito das 109 linhas encostam em fonte oficial, contando as sete parciais. Trinta e quatro
são valor arbitrado para o modelo rodar. Nenhuma das linhas que o módulo atribui ao Manual
Técnico ou ao Technical Manual foi verificada contra o manual em si, porque o manual não foi
aberto nesta tarefa.

## A confirmar com Vitor, que tem os manuais

O módulo diz que massa, geometria, freio, limites de motor e regulamento vêm do Manual
Técnico 991 Fase 1 e 2 e do Technical Manual do 992. A pesquisa externa não alcança nenhum
desses documentos. Os candidatos estão no Drive, em `Trabalho/Porsche_Cup/Docs/`:

| Assunto | Documento no Drive |
|---|---|
| 991.1 e 991.2, ficha geral | `Dados_SSD_Windows/MANUAIS/ENG260410_V5_JOM_Manual 991.1 E 991.2.pdf`, de 2026-04-10 |
| 991.1 e 991.2, versão anterior | `analise_referencias/ENG210319_V4_DAG_Manual 991.1 E 991.2.pdf`, de 2021 |
| 992.1, ficha geral | `Manuais/ENG220308_V8_LUB_Apresentação 992.pdf`, de 2022-03-08 |
| Canais e limites de alarme | `Manuais/Porsche Channels - Mj'E v2.pdf`, e `Dados_SSD_Windows/MANUAIS/ENG260702_V1_MAM_FAIXAS ANALISE VITAIS.pdf` |
| Asa traseira | `Dados_SSD_Windows/MANUAIS/ENQ260610_V2_LUB_ADENDO TÉCNICO ASA.pdf`, de 2026-06-10 |

As sete perguntas abertas, em ordem de impacto no modelo:

1. lf e lr estão trocados nas três gerações. Vitor aprova a troca, ou o manual traz outra
   distribuição de peso que explique os valores atuais?
2. Os 1,920 m e 1,902 m do 992.1 são bitola ou largura de carroceria? Se for largura, qual
   é a bitola de verdade?
3. Qual é o entre-eixos do 992.1 no manual: 2,502 m como está no código, ou 2,459 m como a
   imprensa publica?
4. A massa do 991.2 pronta para corrida é 1.200 kg, como o comunicado oficial diz, ou 1.280
   kg, como o módulo usa?
5. As relações de marcha do 992.1 são mesmo iguais às do 991? O manual traz a tabela?
6. As pressões mínimas de óleo, água e combustível e as temperaturas máximas saíram do
   Porsche Channels Manual ou foram arbitradas?
7. A medida do pneu dianteiro do 991.1 é 245/640-18, 245/650-18 ou 27/65-18?

Enquanto essas sete não fecharem, todo resultado de simulação que use estes presets é
exploratório, e não deve ser comparado com telemetria real como se fosse calibração.

Fontes desta auditoria: `_auditoria/07-pesquisa-simulacao.md` seção 6 e lista de fontes,
`_auditoria/08-fisica-existente.md` seções 3 e 6, e
`_arquivo/saru-physics-py/src/saru_core/vehicle/parameters.py` linha 643. Data: 2026-09-13.
