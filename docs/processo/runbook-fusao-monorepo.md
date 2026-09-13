# Runbook: Fusão do Monorepo SARU

Data: 2026-09-13. Autor: Vitor Toledo / SARU.
Finalidade: instrução executável passo a passo para unificar o repositório institucional e o código da PoC em um único monorepo canônico sem perda de histórico.

## 1. Pré-condições de Segurança

1. Confirmar árvore de trabalho limpa nos dois repositórios locais (`saru` e `saru-poc-trackday`).
2. Confirmar que todos os 284 testes unitários da PoC estão passando em verde:
   ```bash
   cd /home/vitor/Desktop/Motorsport/SARU/saru-poc-trackday && .venv/bin/pytest
   ```
3. Confirmar que os 8 testes de parâmetros físicos do GT3 Cup estão passando em verde:
   ```bash
   cd /home/vitor/Desktop/Motorsport/SARU/saru && python3 -m pytest docs/fisica/test_gt3_cup.py
   ```
4. Confirmar que o remoto canônico definitivo existe na organização: `git@github.com:SARUSySLab/saru.git`. Se ainda estiver como `vitormtt/saru`, transferir para a organização `SARUSySLab` via GitHub UI ou CLI.

## 2. Estrutura Alvo do Monorepo

```
saru/
├── .github/                  # Workflows e automações herdados
├── apps/
│   └── poc-trackday/         # Código executável importado com histórico completo
│       ├── src/saru_poc/
│       ├── web/              # Frontend React
│       ├── tests/            # 284 testes unitários
│       └── seeds/            # Aliases e tracks
├── packages/
│   └── physics/              # Módulos analíticos de dinâmica veicular pura
│       ├── parameters_gt3_cup.py
│       └── tests/
├── docs/                     # Documentação viva consolidada
│   ├── requisitos/           # Requisitos de todas as 5 famílias
│   ├── arquitetura/          # DAS, C4 models, ADRs
│   ├── mocks/                # Protótipos Desktop PC
│   ├── fisica/               # Memoriais de cálculo
│   └── processo/             # Runbooks e normas
├── pyproject.toml            # Workspace unificado gerenciado por uv
└── README.md
```

## 3. Passo a Passo de Execução (para o Claude Code)

Executar a partir da raiz do repositório `saru`:

### Passo 1: Adicionar a PoC como remoto local temporário
```bash
cd /home/vitor/Desktop/Motorsport/SARU/saru
git remote add poc-local /home/vitor/Desktop/Motorsport/SARU/saru-poc-trackday
git fetch poc-local main
```

### Passo 2: Importar a árvore preservando todo o histórico de commits
```bash
git subtree add --prefix apps/poc-trackday poc-local main -m "feat(monorepo): importar saru-poc-trackday para apps/poc-trackday"
```

### Passo 3: Mover módulos de física para packages/physics/
```bash
mkdir -p packages/physics/tests
git mv docs/fisica/parameters_gt3_cup.py packages/physics/
git mv docs/fisica/test_gt3_cup.py packages/physics/tests/
```

### Passo 4: Sincronizar documentos de arquitetura e requisitos
Copiar ou mesclar os documentos de `apps/poc-trackday/docs/` para a pasta central `docs/` mantendo as referências relativas funcionais.

### Passo 5: Unificar workspace Python com uv
Atualizar o arquivo `pyproject.toml` da raiz para declarar o workspace:
```toml
[tool.uv.workspace]
members = ["apps/poc-trackday", "packages/physics"]
```

### Passo 6: Validação integrada
Rodar os testes diretamente da raiz do monorepo:
```bash
uv run pytest apps/poc-trackday/tests
uv run pytest packages/physics/tests
```

### Passo 7: Limpeza e remoção de remotos locais
```bash
git remote remove poc-local
```
Após confirmação de Vitor, mover a pasta antiga `/home/vitor/Desktop/Motorsport/SARU/saru-poc-trackday` para o processo de quarentena.
