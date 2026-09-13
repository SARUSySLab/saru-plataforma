---
titulo: "SARU Ecosystem ADRs"
data: "2026-07-18"
origem: "_arquivo/saru-KB/40_software_arch/adr/README.md"
status: "vigente"
area: "arquitetura_software"
---

# SARU Ecosystem ADRs

Decisões **cross-ecossistema** vivem aqui, **fonte única (single-SoT, ADR-2026-07-15 §7)**. Os
repos NÃO carregam réplica: `saru-physics-py`/`saru-physics-jl` têm apenas um **stub-ponteiro** em
`docs/adr/MASTER_ADR.md`. Decisões escopadas a um serviço vivem no `docs/adr/` do repo dono
(`saru-app`: ADRs locais `0001`-`0014` + master próprio LOCAL do repo).
Números fantasma (`ADR-009/010/011` como cross-eco) são proibidos, cf. convenção no MASTER_ADR.

| Doc | Escopo |
|---|---|
| [MASTER_ADR](MASTER_ADR.md) | Cross-eco: topologia, storage, ISO 8855, 2-tier, convenções (rev 2026-07-16) |
