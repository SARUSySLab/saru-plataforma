---
titulo: "13. Diretrizes de Arquitetura e Calibração"
data: "2026-07-14"
origem: "_arquivo/saru-KB/40_software_arch/modules/14_13_diretrizes_de_arquitetura_e_calibra_o.md"
status: "stale"
area: "fisica"
---

## 13. Diretrizes de Arquitetura e Calibração

> Nota 2026-07-14: diretrizes de pesquisa (~2026-06), parcialmente superadas, o QSS Python é
> **produto** (tier síncrono, ADR-0010 2-tier), não "apenas orquestrador"; o pneu em uso no
> saru-core-jl é **MF6.2** (combined-slip canônico); OpenCRG segue **Horizonte II** (não adotado, > pista hoje é HDF5, cf. módulo 8).

- **Modelagem Acausal:** Migração do Python (QSS, loops causais lentos) para C++/Julia (ModelingToolkit) para lidar com sistemas *stiff* e obter loops <50 ms. O Python deve ser apenas orquestrador.
- **Armazenamento:** Uso obrigatório de HDF5 para telemetria bruta e grids do QSS.
- **Calibração MF5.2+:** Parâmetros essenciais (`pCx1`, etc) calibrados em bancada; delegação pesada de cálculo MF-Swift para C/C++.
- **Single Source of Truth:** OpenCRG é a única fonte da geometria da pista, lida por módulos rápidos, sem passar pelo gargalo do Python no inner-loop.

---
