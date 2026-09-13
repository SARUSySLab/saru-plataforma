# Blueprints de Interface e Mocks para Todas as Famílias SARU

Data: 2026-09-13. Autor: Vitor Toledo / SARU.
Finalidade: especificar a arquitetura de tela, fluxos e componentes visuais para as famílias de produto da SARU que complementam os protótipos N0 e N1 já entregues.

## 1. Visão Geral das Famílias e Mocks

| Família | Perfil de Usuário | Status do Mock | Arquivo Alvo | Resolução Alvo |
|---|---|---|---|---|
| Piloto (N0) | Piloto amador e track day | Entregue (PR #15) | `docs/mocks/mock-piloto-n0-desktop.html` | 1440x900 e 1920x1080 |
| Campeonato e Pitwall (N1) | Organizador e telemetrista | Entregue (PR #15) | `docs/mocks/mock-pitwall-desktop.html` | 1920x1080 widescreen |
| Equipe | Chefe de equipe e mecânico | Especificado abaixo | `docs/mocks/mock-equipe-setup-desktop.html` | 1440x900 e 1920x1080 |
| Engenheiro Avançado | Engenheiro de performance | Especificado abaixo | `docs/mocks/mock-engenheiro-calibracao.html` | 1920x1080 widescreen |
| Aluno / Acadêmica | Estudante de engenharia | Especificado abaixo | `docs/mocks/mock-aluno-didatico.html` | 1440x900 e 1920x1080 |

## 2. Família Equipe: Painel do Chefe de Equipe e Gestão de Setup

### 2.1 Objetivo de Negócio
Permitir que o chefe de equipe e mecânicos gerenciem múltiplos carros da equipe na mesma sessão, controlem a vida útil de componentes críticos e comparem setups mecânicos.

### 2.2 Estrutura do Layout Desktop

```
+------------------------------------------------------------------------------------+
| SARU TEAM OPS | ETAPA: AIC CURITIBA | 2 CARROS ATIVOS (#86 e #11)                  |
+------------------------------------+-----------------------------------------------+
| COLUNA ESQUERDA: GESTÃO MULTICARRO | COLUNA DIREITA: FICHA DE SETUP MECÂNICO       |
|                                    |                                               |
| Carro #86 (Porsche 991.2 Cup)      | Carro Selecionado: #86 (Vitor Toledo)         |
| - Piloto: Vitor Toledo             | - Asa Traseira: Posição 7 (8.2 graus)         |
| - Melhor Volta: 1:24.312 (P2)      | - Barra Dianteira: P3 | Traseira: P2          |
| - Stint Atual: 8 voltas            | - Calibragem Frio: 1.45 bar | Quente: 2.05 bar|
| - Pneus: Jogo Slick 02 (42 km)     | - Altura Dianteira: 78 mm | Traseira: 122 mm  |
|                                    | - Cambagem Dianteira: -3.8° | Traseira: -3.2° |
| Carro #11 (Porsche 991.2 Cup)      |                                               |
| - Piloto: Lucas Antunes            | TABELA DE CONSUMÍVEIS E VIDA ÚTIL             |
| - Melhor Volta: 1:24.089 (P1)      | - Pastilhas Dianteiras: 68% de vida restante  |
| - Stint Atual: 10 voltas           | - Discos de Freio: 412 km rodados (OK)        |
| - Pneus: Jogo Slick 01 (78 km)     | - Óleo de Câmbio: 18 horas de motor           |
+------------------------------------+-----------------------------------------------+
| FAIXA INFERIOR: COMPARATIVO DIRETO ENTRE COMPANHEIROS DE EQUIPE                    |
| Delta #86 vs #11: +0.223s | #86 perde 0.15s na C1 e ganha 0.08s na C5            |
+------------------------------------------------------------------------------------+
```

### 2.3 Componentes Críticos
1. Matriz de setup com validação física (limites mecânicos do Porsche 911 GT3 Cup).
2. Marcador visual de desgaste por cores (verde para vida útil normal, amarelo para atenção, vermelho para troca mandatória).
3. Comparativo de telemetria entre companheiros no mesmo chassi.

## 3. Família Engenheiro Avançada: Calibração e Engenharia Reversa

### 3.1 Objetivo de Negócio
Fornecer ao engenheiro de pista ferramentas analíticas para estimar parâmetros desconhecidos do veículo a partir de voltas reais ou simuladas (atendendo ao requisito E-RF-09).

### 3.2 Painéis do Módulo
1. Estimador de Massa ($M$):
   - Gráfico de dispersão entre força longitudinal de tração nas rodas ($F_x$) e aceleração medida ($a_x$).
   - Regressão linear por mínimos quadrados fornecendo a massa efetiva calculada e intervalo de confiança.
2. Estimador de Arrasto Aerodinâmico ($CdA$):
   - Análise de desaceleração em reta por coastdown (embreagem acionada ou corte de aceleração em alta velocidade).
   - Ajuste da curva quadrática de resistência do ar.
3. Estimador de Rigidez de Rolagem ($k_{\phi}$):
   - Razão entre ângulo de rolagem da carroceria medido por potenciômetros de suspensão e aceleração lateral ($a_y$).

## 4. Família Aluno e Acadêmica: Trilha Didática Guiada

### 4.1 Objetivo de Negócio
Ensinar dinâmica veicular aplicada a estudantes e novatos utilizando seus próprios arquivos de telemetria (MoTeC, AiM, Assetto Corsa ou iRacing).

### 4.2 Módulos da Trilha
1. Módulo 1: Círculo de Atrito de Kamm.
   - O aluno visualiza graficamente como a aderência do pneu é dividida entre freio, tração e curva.
2. Módulo 2: Transferência de Carga Dinâmica.
   - Demonstração da variação da força vertical nas quatro rodas durante frenagem e aceleração.
3. Módulo 3: Subesterço e Sobreesterço.
   - Cálculo automático do gradiente de esterço com base na velocidade de guinada e ângulo de volante.

## 5. Roteiro de Implementação para o Claude Code

1. O Claude Code poderá criar os arquivos HTML correspondentes em `docs/mocks/` utilizando a mesma folha de estilo base do N0.
2. Cada mock deve reutilizar as classes tipográficas (`tabular`), a paleta do `tokens.css` e manter o foco estrito em desktop (resoluções 1440x900 e 1920x1080).
