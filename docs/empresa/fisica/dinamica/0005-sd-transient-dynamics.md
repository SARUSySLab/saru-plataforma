---
titulo: "ADR-0005, Dinâmica transiente do produto SD (3-DOF no core) e dono do 14-DOF"
data: "2026-08-11"
origem: "_arquivo/saru-app/docs/adr/0005-sd-transient-dynamics.md"
status: "vigente"
area: "dinamica_veicular"
---

# ADR-0005, Dinâmica transiente do produto SD (3-DOF no core) e dono do 14-DOF

- **Status:** Aceito, 2026-06-26
- **Escopo:** repo `saru-os` (engine `/simulate`) + `saru-core` (`dynamics/`)
- **Relacionadas:** [ADR-0002](0002-borda-nestjs-engine-python.md) (engine embrulha saru-core)

## Contexto

O `POST /api/simulate` (produto **SD**, handling/manobras: step/DLC/fishhook/sweep → yaw_rate,
roll, pitch, lateral_velocity) era um **mock numpy inline** que **duplicava** exatamente
`saru_core.dynamics.analytical.simulate_analytical_maneuver` (mesma heurística de constantes de
tempo). Pesquisa também revelou que:

- O **14-DOF de alta fidelidade** (`Chassis14DOF`) mora no repo **externo** `chassis-solver`
  (pacote `saru_chassis`), **não** no `saru-core`.
- O `saru-core` carregava uma **cópia órfã quebrada** (`dynamics/solver_14dof.py` + `simulation/rl_driver/`)
  que importava `saru_chassis.*` (ImportError), código morto.
- Havia, portanto, **três** esforços 14-DOF na órbita (Julia `saru-core-jl`, Python externo
  `chassis-solver`, a cópia órfã), risco do anti-padrão de duplicação ("monstro").

## Decisão

1. **De-duplicar:** o engine `/simulate` **delega ao `saru-core.dynamics`** (não reimplementa
   física). Flag `model`: `analytical` (default, heurístico) | `transient3dof` (físico real).
2. **Modelo físico do SD = 3-DOF no core:** `saru_core.dynamics.simulate_transient_3dof`, bicycle
   (lateral/yaw) + 1 DOF de rolagem, reusando o `SARUSolver`. Enxuto e **suficiente** para o produto
   SD (manobras de handling).
3. **Dono do 14-DOF = externo (`chassis-solver`) + Julia (`saru-core-jl`).** NÃO o `saru-core`.
   A cópia órfã quebrada (`solver_14dof.py` + `rl_driver/`) foi **removida** do `saru-core`.

## Consequências

- Uma única fonte da física de manobra (no `saru-core`); o engine é fino.
- Os números do `transient3dof` são reais mas **não calibrados** contra dados de pista (trilha à
  parte, como o QSS).
- Integração futura do 14-DOF de verdade (chassis-solver/Julia) entra **atrás do mesmo contrato**
  `/simulate` (novo valor de `model`), sem reescrever o engine.
- Física é CPU-bound → o handler async faz `asyncio.to_thread` (não bloqueia o event loop).
