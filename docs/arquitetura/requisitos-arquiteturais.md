# Requisitos arquiteturais

Restrições derivadas diretamente dos requisitos não funcionais e regras de negócio da família Piloto. Cada requisito condiciona a estrutura física, os padrões de projeto ou a persistência do sistema.

## Matriz de restrições arquiteturais

| Id | Requisito motivador | O que exige na arquitetura | O que descarta na arquitetura |
|---|---|---|---|
| ARQ-01 | PIL-RNF-01, PIL-RN-01 | Degradação graciosa com tipagem estrita de falha parcial (`MotivoDegradacao`) | Exceções não tratadas derrubando o pipeline inteiro; valores padrão silenciosos |
| ARQ-02 | PIL-RNF-02, PIL-RN-04, PIL-RN-05 | Imutabilidade do dado bruto e idempotência de ingestão via hash SHA-256 | Sobrescrita de arquivos originais; mutação de séries temporais históricas |
| ARQ-03 | PIL-RNF-03 | Desacoplamento entre interface HTTP e processamento via fila assíncrona (resposta 202 Accepted) | Processamento síncrono bloqueando a rota HTTP durante parsing de telemetria |
| ARQ-04 | PIL-RNF-04 | Camada de abstração de armazenamento de objetos isolada por variável de ambiente `SARU_DATA_ROOT` | Acoplamento direto do pipeline ao sistema de arquivos local ou a SDKs proprietários |
| ARQ-05 | PIL-RNF-06 | Validação de borda de saída com esquemas Pydantic espelhando contratos TypeScript | Entrega de dicionários soltos ou formatos heterogêneos para a interface web |
| ARQ-06 | PIL-RNF-07, E-RN-05 | Isolamento multitenant estrito por dono em todas as consultas SQL e cookies HTTP-only com JWT | Consultas sem filtro de usuário; armazenamento de senhas em texto puro |
| ARQ-07 | PIL-RNF-08, E-RNF-06 | Camada de geração de relatórios orientada a métricas sintetizadas legíveis em menos de 5 segundos | Exibição de dezenas de gráficos analíticos brutos para o piloto no box |
| ARQ-08 | PIL-RNF-09, PIL-RN-10 | Séries temporais persistidas estritamente no Sistema Internacional de Unidades (SI) | Conversão ad-hoc de unidades no banco ou mistura de grandezas (ex. nós, psi) no núcleo |
| ARQ-09 | PIL-RNF-11 | Execução autocontida em container único servindo API FastAPI e frontend estático | Arquiteturas distribuídas de microsserviços pesados para o ambiente da PoC |
| ARQ-10 | PIL-RN-06, PIL-RN-16, PIL-RN-17 | Resolução de autódromo em pipeline de três estágios com desempate por layout e bypass para simuladores | Dependência exclusiva de geolocalização por GPS ou coordenadas simuladas falsas |
| ARQ-11 | PIL-RN-07, PIL-RN-12 | Máquina de estados para corte e classificação explícita de voltas anômalas (in-lap, out-lap, aquecimento, tráfego) | Descarte cego de voltas fora do padrão sem categorização no relatório final |
| ARQ-12 | PIL-RN-13 | Módulo desacoplado de decomposição de frenagem e trail-braking via cinemática veicular | Mistura de heurísticas de pilotagem dentro dos parsers de arquivo binário |
