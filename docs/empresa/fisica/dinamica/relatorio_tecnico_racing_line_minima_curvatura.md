---
titulo: "Relatório técnico, racing line por mínima curvatura"
data: "2026-08-11"
origem: "_arquivo/saru-app/docs/research/relatorio_tecnico_racing_line_minima_curvatura.md"
status: "vigente"
area: "dinamica_veicular"
---

# Relatório técnico, racing line por mínima curvatura

## Escopo

Este relatório consolida e valida a pesquisa sobre geração de racing line por mínima curvatura, com foco em uma implementação em Julia usando QP esparso, por exemplo OSQP.jl, ou álgebra linear. Foram consultados artigos originais, preprints, documentação de projetos abertos e fontes em inglês, português e chinês.

A conclusão mais importante é de atribuição: Braghin et al. (2008) apresentam um modelo de piloto e uma otimização geométrica baseada em caminho mínimo e curvatura mínima, mas não devem ser descritos simplesmente como os autores de uma única formulação moderna `d_i`-normal + `κ = κ₀ + A d` resolvida por OSQP. A formulação QP iterativa com offsets laterais, aproximação convexa da curvatura e implementação TUMFTM está mais diretamente associada a Heilmeier et al. e ao código TUMFTM.

---

## 1. Fontes consultadas e grau de confiança

### Fontes primárias

1. **Braghin, Cheli, Melzi e Sabbioni, “Race driver model”, Computers & Structures, 2008.**
   - Fonte do modelo de piloto e da ideia de combinar caminho curto e caminho de menor curvatura.
   - A formulação original usa pontos entre as bordas e o parâmetro de posição lateral; não é idêntica à implementação TUM moderna por offset normal.
   - DOI: [10.1016/j.compstruc.2007.04.028](https://doi.org/10.1016/j.compstruc.2007.04.028).

2. **Heilmeier et al., “Minimum curvature trajectory planning and control for an autonomous race car”.**
   - Fonte principal para a formulação moderna de mínima curvatura por QP, sua implementação iterativa e o pipeline de trajetória/controle.
   - DOI: [10.1080/00423114.2019.1631455](https://doi.org/10.1080/00423114.2019.1631455).

3. **Kapania, Subosits e Gerdes, “A Sequential Two-Step Algorithm for Fast Generation of Vehicle Racing Trajectories”.**
   - Artigo publicado no Journal of Dynamic Systems, Measurement, and Control, 2016; preprint [arXiv:1902.00606](https://arxiv.org/abs/1902.00606).
   - O método alterna perfil de velocidade forward/backward e QP de caminho com dinâmica afim variante no tempo.

4. **TUMFTM/global_racetrajectory_optimization.**
   - Repositório aberto com shortest path, minimum curvature, minimum curvature iterativo, minimum time e variantes com powertrain.
   - [GitHub](https://github.com/TUMFTM/global_racetrajectory_optimization).

5. **TUMFTM/trajectory_planning_helpers.**
   - Implementa `opt_min_curv`, `opt_shortest_path`, `iqp_handler`, splines de terceira ordem, cálculo analítico e numérico de curvatura, interpolação e perfil de velocidade.
   - [GitHub](https://github.com/TUMFTM/trajectory_planning_helpers).

6. **CommonRoad Raceline Planner, Minimum Curvature Planner.**
   - Port da abordagem FTM/TUM; documenta explicitamente que a mínima curvatura é uma aproximação convexa resolvida por QP e informa o erro máximo entre a curvatura linearizada e a original.
   - [Documentação](https://commonroad-raceline-planner-feb47b.pages.gitlab.lrz.de/mcp/).

### Fontes secundárias e independentes

7. **Bari et al., “Factor Graph-Based Planning as Inference for Autonomous Vehicle Racing”, arXiv:2203.03224, versão 2024.**
   - Compara shortest path, minimum curvature e minimum time.
   - Afirma explicitamente que Braghin usa otimização geométrica, Kapania divide o problema em dois passos e Heilmeier formula um QP iterativo.
   - [PDF](https://arxiv.org/pdf/2203.03224.pdf).

8. **SciTePress, “Study of Track Segmentation for Lap Time Optimization”, 2024.**
   - Exemplo independente que combina spline cúbica, racing line de Braghin e perfil de velocidade de Kapania.
   - [PDF](https://www.scitepress.org/Papers/2024/127286/127286.pdf).

9. **Bari et al. / literatura de fator gráfico.**
   - Oferece uma alternativa não-QP tradicional: fatores locais de curvatura, mínimos quadrados e Levenberg-Marquardt.

10. **Fonte em chinês sobre `trajectory_planning_helpers`.**
    - Confirma a presença de `opt_min_curv`, `opt_shortest_path`, splines de terceira ordem e cálculo analítico/numérico de curvatura.
    - [CSDN](https://blog.csdn.net/gitblog_00034/article/details/139850348).

---

## 2. Correção de atribuição: Braghin versus Heilmeier/TUM

A resposta curta é:

- Braghin et al.: modelo de piloto e otimização geométrica de trajetória; considera caminho mínimo e mínima curvatura, normalmente representando o ponto da linha entre os limites esquerdo e direito por um parâmetro lateral.
- Heilmeier et al.: formulação QP de mínima curvatura usada no ecossistema TUMFTM, com aproximação convexa, limites de pista, splines e chamada iterativa.
- Kapania et al.: algoritmo de dois passos com perfil de velocidade e atualização do caminho através de QP com modelo de veículo.
- TUMFTM: implementação aberta que reúne essas ideias, com nomenclatura e detalhes de discretização próprios.

Portanto, é incorreto afirmar que toda a matriz `A` da linearização exata abaixo é “a matriz de Braghin”. Ela é uma construção consistente e útil para a implementação moderna, mas a documentação/código TUM geralmente usa uma aproximação matricial baseada em derivadas, e a formulação original de Braghin usa outra parametrização.

---

## 3. Parametrização por offset normal

Considere uma referência fechada:

\[
c_i = [x_i^c,y_i^c]^T, \quad i=0,\ldots,N-1.
\]

Após reamostragem em comprimento de arco uniforme `h`, calcule:

\[
t_i = \frac{c_{i+1}-c_{i-1}}{\|c_{i+1}-c_{i-1}\|},
\qquad
n_i=[-t_{y,i},t_{x,i}]^T.
\]

A linha é:

\[
p_i=c_i+n_i d_i,
\]

ou:

\[
x=x^c+N_xd,
\qquad y=y^c+N_yd,
\]

onde `N_x = Diagonal(n_x)` e `N_y = Diagonal(n_y)`.

Se a normal aponta para a esquerda, os limites são:

\[
-w_{R,i}\le d_i\le w_{L,i}.
\]

É recomendável subtrair uma margem de segurança `m_i`:

\[
-(w_{R,i}-m_i)\le d_i\le w_{L,i}-m_i.
\]

A restrição deve entrar no solver como box constraint. Resolver sem restrição e aplicar `clamp` posteriormente não é equivalente ao QP constrained.

---

## 4. Matrizes de diferenças periódicas

Para pontos uniformemente espaçados:

\[
(D_1z)_i=\frac{z_{i+1}-z_{i-1}}{2h},
\]

\[
(D_2z)_i=\frac{z_{i+1}-2z_i+z_{i-1}}{h^2}.
\]

Os índices são módulo `N`. Cada linha de `D_1` tem o stencil `[-1,0,+1]/(2h)` e cada linha de `D_2` tem `[+1,-2,+1]/h²`.

Para a referência:

\[
x'_0=D_1x^c,\quad y'_0=D_1y^c,
\]

\[
x''_0=D_2x^c,\quad y''_0=D_2y^c.
\]

Como a linha depende linearmente de `d`:

\[
x'=x'_0+D_1N_xd,
\quad y'=y'_0+D_1N_yd,
\]

\[
x''=x''_0+D_2N_xd,
\quad y''=y''_0+D_2N_yd.
\]

---

## 5. Curvatura geométrica linearizada

A curvatura é:

\[
\kappa_i=\frac{x'_iy''_i-y'_ix''_i}{(x_i'^2+y_i'^2)^{3/2}}.
\]

Na trajetória de referência, defina:

\[
V_i=x_{0,i}'^2+y_{0,i}'^2,
\]

\[
N_i=x_{0,i}'y_{0,i}''-y_{0,i}'x_{0,i}'',
\]

\[
\kappa_{0,i}=N_i/V_i^{3/2}.
\]

A variação é:

\[
\delta\kappa_i=
\frac{\delta N_i}{V_i^{3/2}}
-
\frac{3N_i}{V_i^{5/2}}
(x'_{0,i}\delta x'_i+y'_{0,i}\delta y'_i).
\]

Além disso:

\[
\delta N_i=
 y''_{0,i}\delta x'_i+x'_{0,i}\delta y''_i
-x''_{0,i}\delta y'_i-y'_{0,i}\delta x''_i.
\]

Defina:

\[
X_1=D_1N_x,\quad Y_1=D_1N_y,
\]

\[
X_2=D_2N_x,\quad Y_2=D_2N_y.
\]

A matriz `A` em:

\[
\kappa\approx\kappa_0+Ad
\]

é:

\[
A=S_1[
\operatorname{diag}(y_0'')X_1
+\operatorname{diag}(x_0')Y_2
-\operatorname{diag}(x_0'')Y_1
-\operatorname{diag}(y_0')X_2]
\]

\[
\qquad -S_2[
\operatorname{diag}(x_0')X_1
+\operatorname{diag}(y_0')Y_1],
\]

com:

\[
S_1=\operatorname{diag}(V^{-3/2}),
\qquad
S_2=\operatorname{diag}(3NV^{-5/2}).
\]

`A` é `N × N`. Com diferenças centradas, cada linha tem suporte aproximadamente em `i-2` até `i+2`, com wrap-around periódico.

Essa é a linearização da curvatura geométrica verdadeira. Ela não deve ser confundida com a aproximação quadrática mais simples usada em muitos códigos TUM.

---

## 6. QP por segunda derivada cartesiana

A aproximação convexa comum é minimizar:

\[
J_\kappa=
\|x''\|_2^2+\|y''\|_2^2.
\]

Defina:

\[
B_x=D_2N_x,
\qquad B_y=D_2N_y.
\]

Então:

\[
J_\kappa=
\|x_0''+B_xd\|^2
+\|y_0''+B_yd\|^2.
\]

Na convenção do OSQP:

\[
\min_d \frac12d^THd+f^Td,
\]

com:

\[
H=B_x^TB_x+B_y^TB_y,
\]

\[
f=B_x^Tx_0''+B_y^Ty_0''.
\]

Dependendo da expansão usada, `H` e `f` podem aparecer multiplicados por 2; isso não altera o minimizador se ambos forem escalados consistentemente.

Essa formulação é convexa diretamente e normalmente não requer relinearização da curvatura, embora a recomputação de normais e a chamada iterativa melhorem a fidelidade.

---

## 7. QP com curvatura linearizada

Use:

\[
\min_d
\frac12\|W_\kappa(\kappa_0+Ad)\|^2
+\frac{\lambda_2}{2}\|D_2d\|^2
+\frac{\lambda_1}{2}\|D_1d\|^2
+\frac{\lambda_s}{2}\|d-d_{ref}\|^2.
\]

A Hessiana e o vetor linear são:

\[
H=A^TW_\kappa^2A
+\lambda_2D_2^TD_2
+\lambda_1D_1^TD_1
+\lambda_sI,
\]

\[
f=A^TW_\kappa^2\kappa_0-
\lambda_sd_{ref}.
\]

As restrições são:

\[
\ell_i\le d_i\le u_i.
\]

Trust region opcional:

\[
|d_i-d_i^{old}|\le\Delta_i.
\]

Na prática:

\[
\ell_i=\max[-(w_{R,i}-m_i),d_i^{old}-\Delta_i],
\]

\[
 u_i=\min[w_{L,i}-m_i,d_i^{old}+\Delta_i].
\]

A trust region é especialmente importante porque `κ₀ + A d` só é uma aproximação local.

---

## 8. Iteração externa

Pseudocódigo validado conceitualmente:

```text
input: closed track, widths, spacing h
resample track uniformly in arc length
smooth reference periodically
compute initial d = 0
set trust radius Δ

repeat:
    construct current path c + n*d
    recompute periodic tangent and normals
    construct D1 and D2

    either:
        compute κ0 and A
        H = A' Wκ² A + λ2 D2'D2 + λ1 D1'D1
        f = A' Wκ² κ0
    or:
        Bx = D2*Nx
        By = D2*Ny
        H = Bx'Bx + By'By + regularization
        f = Bx'x0'' + By'y0''

    lower = max(track lower bound, d - Δ)
    upper = min(track upper bound, d + Δ)

    solve QP:
        minimize 1/2*d_new'*H*d_new + f'*d_new
        subject to lower <= d_new <= upper

    construct candidate path
    evaluate exact nonlinear curvature and objective

    if candidate improves objective:
        accept d_new
        optionally increase Δ
    else:
        reject candidate
        reduce Δ
    end

until:
    norm(d_new-d, Inf)/max(1,norm(d,Inf)) < 1e-3
    and relative objective change < 1e-4
    and curvature linearization error is acceptable

return final path
```

O número de iterações não é uma constante do método. O repositório TUM expõe uma chamada iterativa (`iqp_handler`), mas o número adequado depende da pista, da suavização e da inicialização. Kapania relata convergência do lap time em cerca de 4-5 iterações no circuito de 4,5 km; portanto, usar “3 iterações sempre” não é uma regra geral.

Critérios recomendados:

\[
\frac{\|d^{k+1}-d^k\|_\infty}{\max(1,\|d^k\|_\infty)}<10^{-3},
\]

\[
\frac{|J^{k+1}-J^k|}{\max(1,|J^k|)}<10^{-4}.
\]

Também compare:

\[
\|\kappa_{nonlinear}-(\kappa_0+Ad)\|_\infty.
\]

---

## 9. Kapania-Subosits-Gerdes

O método é uma decomposição iterativa:

1. dado um caminho, calcula perfil de velocidade mínimo-tempo;
2. dada a velocidade, atualiza o caminho por otimização convexa;
3. repete até o lap time deixar de melhorar.

A descrição oficial do preprint diz explicitamente que o primeiro passo usa integração forward/backward sujeito às restrições de pneu e que o segundo resolve uma otimização convexa de caminho, minimizando curvatura, respeitando a pista e uma dinâmica afim variante no tempo.

### Perfil de velocidade

Uma aproximação lateral inicial é:

\[
U_x(s)\le\sqrt{\frac{\mu g}{|\kappa(s)|}}.
\]

A passagem para frente impõe aceleração:

\[
U_{i+1}=\sqrt{U_i^2+2a_{x,max,i}\Delta s},
\]

e a passagem para trás impõe frenagem:

\[
U_{i-1}=\sqrt{U_i^2-2a_{x,brake,i}\Delta s}.
\]

Os limites são combinados com o envelope de força do veículo.

### QP de caminho

O modelo linearizado discreto é:

\[
x_{i+1}=A_ix_i+B_i\delta_i+d_i,
\]

com estados como erro lateral, erro de orientação, sideslip e yaw rate. O problema impõe:

\[
w_{out,i}\le e_i\le w_{in,i},
\]

limites de slip angles, steering e eventualmente taxa de steering, enquanto minimiza uma medida de curvatura/variação de orientação.

Essa formulação não é equivalente a um QP apenas em `d_i`; é um QP de estados, controles e dinâmica de veículo.

O artigo não oferece garantia de ótimo global nem de convergência, mas reporta desempenho experimental no Thunderhill Raceway. A versão disponível no arXiv informa aproximadamente 4-5 iterações e cerca de 30 s por iteração no circuito de 4,5 km em um laptop.

---

## 10. Espaçamento não uniforme

Não use `[1,-2,1]/h²` se `h` varia significativamente. Para:

\[
h_-=s_i-s_{i-1},\qquad h_+=s_{i+1}-s_i,
\]

use:

\[
x_i'= -\frac{h_+}{h_-(h_-+h_+)}x_{i-1}
+\frac{h_+-h_-}{h_-h_+}x_i
+\frac{h_-}{h_+(h_-+h_+)}x_{i+1},
\]

\[
x_i''=\frac{2}{h_-(h_-+h_+)}x_{i-1}
-\frac{2}{h_-h_+}x_i
+\frac{2}{h_+(h_-+h_+)}x_{i+1}.
\]

Use os mesmos coeficientes para `y`. O tratamento cíclico deve ser aplicado também nos pontos inicial e final.

A recomendação prática é reparametrizar por comprimento de arco e reamostrar uniformemente antes de montar o QP. O TUM possui funções de interpolação de pista, splines e interpolação das larguras.

---

## 11. Fechamento da volta

Todos os operadores devem ser periódicos:

\[
d_{-1}=d_{N-1},\quad d_N=d_0.
\]

Isso inclui derivadas, curvatura, custo de suavidade e normais. `atan2` deve ser seguido de `unwrap` antes de derivar headings.

Uma implementação não periódica frequentemente cria um pico artificial de curvatura na junção `N-1 -> 0`. Para trajetórias de várias voltas, também é útil adicionar dois ou mais fatores/linhas de continuidade além do fim da janela, como observado na literatura de planejamento local.

---

## 12. Suavização e numérica

A segunda derivada amplifica ruído. Pipeline recomendado:

1. remover pontos duplicados;
2. parametrizar por comprimento de arco;
3. aplicar spline periódica ou filtro suave;
4. reamostrar em `h` constante;
5. recalcular tangentes e normais;
6. reduzir as larguras pela margem de segurança;
7. verificar cruzamento de normais;
8. montar o QP.

Para `N ≈ 10³`:

- `D2'D2` é banda-cíclica;
- a matriz é esparsa;
- OSQP é adequado;
- simetrize `H` com `(H+H')/2`;
- adicione `εI`, por exemplo `10^-8`-`10^-5`, se necessário;
- escale curvatura, offset e pesos para evitar disparidade de ordens de grandeza.

Verifique sempre:

- status do solver;
- primal residual;
- dual residual;
- distância mínima às bordas;
- cruzamento de normais;
- curvatura máxima;
- erro entre curvatura aproximada e não linear;
- continuidade na junção da volta.

---

## 13. TUMFTM: o que o código realmente oferece

O README do projeto lista:

- shortest path;
- minimum curvature sem chamada iterativa;
- minimum curvature com chamada iterativa;
- minimum time;
- minimum time com comportamento do powertrain.

O próprio projeto observa que a linha de mínima curvatura é próxima da linha de mínimo tempo nas curvas, mas difere quando as limitações de aceleração do veículo passam a ser relevantes. A otimização de mínimo tempo exige muito mais parâmetros e computação.

O projeto também documenta que suas normais normalmente apontam para a direita no sentido de condução. Portanto, os sinais dos offsets no TUM podem ser opostos aos de uma implementação que define a normal como `[-ty,+tx]`.

A saída LTPL contém explicitamente:

- referência `x_ref`, `y_ref`;
- larguras direita/esquerda;
- normal `x_normvec`, `y_normvec`;
- deslocamento lateral `alpha_m`;
- distância, heading e curvatura da racing line;
- velocidade e aceleração.

O TUM utiliza splines de terceira ordem para diversas operações e fornece curvatura analítica via spline, além de curvatura numérica. Isso é importante: a discretização do QP e o cálculo final de curvatura podem não usar exatamente o mesmo operador de diferenças finitas.

---

## 14. CommonRoad Raceline Planner

O `MinimumCurvaturePlanner` do CommonRoad documenta que:

- usa otimização convexa por QP;
- minimiza uma aproximação convexa da curvatura;
- é baseado no projeto TUMFTM;
- fornece um `maximum_curvature_error` entre a aproximação linearizada e a curvatura original.

Isso valida a recomendação de avaliar explicitamente o erro de linearização, em vez de assumir que o QP é exatamente equivalente à curvatura geométrica não linear.

---

## 15. Formulação recomendada para Julia

Para uma primeira implementação confiável:

### Versão A, TUM-like

\[
H=B_x^TB_x+B_y^TB_y+\lambda_2D_2^TD_2+\lambda_sI,
\]

\[
f=B_x^Tx''_0+B_y^Ty''_0-\lambda_sd_{old},
\]

\[
\ell\le d\le u.
\]

Vantagens: convexa, esparsa, simples, próxima do ecossistema TUM.

### Versão B, curvatura linearizada

\[
H=A^TW_\kappa^2A+\lambda_2D_2^TD_2+\lambda_sI,
\]

\[
f=A^TW_\kappa^2\kappa_0-\lambda_sd_{old},
\]

com limites de pista e trust region.

Vantagens: aproxima melhor a curvatura verdadeira; requer relinearização e controle de passo.

### Versão C, mínimo tempo

Usar a versão A ou B como inicialização e depois resolver um problema de velocidade/forças, como TUM minimum-time ou Kapania-Gerdes. A mínima curvatura não é um substituto geral para mínimo tempo: ela não representa diretamente aceleração, frenagem, powertrain, carga aerodinâmica ou distribuição de força.

---

## 16. Checklist de validação

Antes de confiar na linha:

- `d_i` respeita os limites laterais em todos os pontos?
- as normais não se cruzam?
- a volta fecha em posição, heading e curvatura?
- a curvatura numérica coincide com a curvatura da spline?
- a linha não entra na pista por causa de uma normal longa demais?
- `H` é simétrica e positiva semidefinida?
- OSQP informa `solved` ou `solved inaccurate` aceitável?
- a solução muda pouco ao reduzir `h`?
- a solução é estável ao variar `λ2`?
- a velocidade do lap-time simulator foi recalculada usando a curvatura final, não a curvatura do centroline?
- a linha de mínima curvatura realmente reduz o lap time no seu modelo, em vez de apenas reduzir `∑κ²`?

---

## 17. Referências

- Braghin, F., Cheli, F., Melzi, S., Sabbioni, E. “Race driver model”. Computers & Structures, 86(13-14), 1503-1516, 2008. DOI: [10.1016/j.compstruc.2007.04.028](https://doi.org/10.1016/j.compstruc.2007.04.028).
- Heilmeier, A., Wischnewski, A., Hermansdorfer, L., Betz, J., Lienkamp, M., Lohmann, B. “Minimum curvature trajectory planning and control for an autonomous race car”. Vehicle System Dynamics, 58(10), 1497-1527. DOI: [10.1080/00423114.2019.1631455](https://doi.org/10.1080/00423114.2019.1631455).
- Kapania, N. R., Subosits, J., Gerdes, J. C. “A Sequential Two-Step Algorithm for Fast Generation of Vehicle Racing Trajectories”. Journal of Dynamic Systems, Measurement, and Control, 138(9), 091005, 2016. Preprint: [arXiv:1902.00606](https://arxiv.org/abs/1902.00606).
- TUMFTM. [global_racetrajectory_optimization](https://github.com/TUMFTM/global_racetrajectory_optimization).
- TUMFTM. [trajectory_planning_helpers](https://github.com/TUMFTM/trajectory_planning_helpers).
- CommonRoad. [commonroad-raceline-planner](https://commonroad-raceline-planner-feb47b.pages.gitlab.lrz.de/mcp/).
- Bari, S., Wang, X., Haidari, A. S., Wollherr, D. “Factor Graph-Based Planning as Inference for Autonomous Vehicle Racing”. [arXiv:2203.03224](https://arxiv.org/pdf/2203.03224.pdf).
- SciTePress. “Study of Track Segmentation for Lap Time Optimization”. [PDF](https://www.scitepress.org/Papers/2024/127286/127286.pdf).
- NYU. “Planning Paths of Minimal Curvature”. [Technical report](https://cs.nyu.edu/media/publications/TR1994-672.pdf).

---

## Conclusão operacional

Para o projeto em Julia, implemente primeiro a formulação TUM-like com `D2`, limites laterais explícitos, matriz esparsa cíclica e avaliação posterior da curvatura por spline. Depois acrescente a versão `κ₀ + A d` como uma segunda etapa, protegida por trust region e critério de erro de linearização. Use Kapania-Gerdes apenas quando o objetivo passar de “linha geometricamente suave” para “trajetória coerente com dinâmica longitudinal/lateral e lap time”.
