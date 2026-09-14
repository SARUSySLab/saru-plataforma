---
titulo: "15. Padrões de Código e AI Workflows (Claude Blueprint)"
data: "2026-07-14"
origem: "_arquivo/saru-KB/40_software_arch/modules/16_15_padr_es_de_c_digo_e_ai_workflows_claude_blueprint.md"
status: "vigente"
area: "ia_agentes"
---

## 15. Padrões de Código e AI Workflows (Claude Blueprint)

- **Workflow (Explore -> Plan -> Code -> Commit):** Zero *vibe coding*. O agente de IA deve criar planos antes de codificar (SDD/ADRs). `TODO(human)` deve ser usado em bifurcações críticas arquiteturais.
- **Regras para a pasta `.claude/`:** `CLAUDE.md` super enxuto (<60 linhas); regras por path (ex: `rules/cpp.md`); divisão de agentes (`plan-architect`, `debug-mentor`) e Hooks determinísticos (como auto-formatadores bloqueando commits sujos).
- **C++/Pybind11:** Respeito restrito ao RAII, visibilidade oculta nos módulos pybind11 e cuidado extremo nas cópias via `Eigen <-> NumPy`.

- **OWASP LLM Top 10 e Sanitização:** O framework blinda os riscos gerados por agentes de codificação (Injeção Indireta de Prompt e Exposição de Dados). Mitigação via ambientes KVM/Bubblewrap para sandboxing e inibição de bypass de segurança.

---
