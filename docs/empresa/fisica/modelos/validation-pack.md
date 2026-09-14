---
titulo: "Physics Validation Pack"
data: "2026-07-08"
origem: "_arquivo/saru-docs/docs/fisica/validation-pack.md"
status: "vigente"
area: "fisica"
---

# Physics Validation Pack

Este pack define como Vitor e qualquer pessoa mexendo em fisica devem trabalhar
para o MVP. O objetivo nao e burocracia; e impedir que produto, codigo e
marketing usem claims sem evidencia.

## Principio central

Claim fisico so entra no produto se tiver:

- fonte ou fixture;
- unidade;
- canal;
- teste;
- tolerancia;
- nivel de confianca.

## Niveis de claim

| Nivel | Significado | Pode ir para demo? | Pode ir para marketing? |
|---|---|---:|---:|
| `draft` | Ideia/modelo ainda sem fixture. | Nao | Nao |
| `supported` | Existe fixture e tendencia coerente. | Sim, com ressalva | Sim, linguagem conservadora |
| `validated` | Comparacao por canal, tolerancia e revisao aprovadas. | Sim | Sim |
| `rejected` | Evidencia contradiz ou qualidade insuficiente. | Nao | Nao |

## Matriz canonica de canais do MVP

| Canal canonico | Unidade interna | Obrigatorio? | Uso | Regras de qualidade |
|---|---|---:|---|---|
| `time_s` | s | Sim | timebase | monotonic, sem saltos negativos |
| `distance_m` | m | Preferencial | alinhamento por pista | monotonic por volta ou reconstruivel |
| `speed_mps` | m/s | Sim | delta, braking, acceleration | valor positivo, coerente com distancia/time |
| `throttle_pct` | % | Preferencial | pickup, lift, coasting | 0 a 100 |
| `brake_pct` | % | Preferencial | braking point, release | 0 a 100 |
| `steering_deg` | deg | Preferencial | consistencia, under/oversteer proxy | sinal/offset documentado |
| `gear` | integer | Opcional | contexto de pilotagem | valores discretos coerentes |
| `rpm` | rpm | Opcional | powertrain context | positivo, faixa plausivel |
| `lat_acc_mps2` | m/s^2 | Opcional | cornering | unidade clara |
| `long_acc_mps2` | m/s^2 | Opcional | braking/accel | unidade clara |
| `gps_lat` | deg | Opcional | pista/mapa | range geografico valido |
| `gps_lon` | deg | Opcional | pista/mapa | range geografico valido |

## Quality flags

| Flag | Significado | Acao |
|---|---|---|
| `ok` | Canal confiavel para o uso atual. | Pode entrar em analise/export. |
| `missing` | Canal esperado nao existe. | Mostrar lacuna na UI. |
| `unit_unknown` | Unidade ausente ou ambigua. | Bloquear claim tecnico. |
| `sample_rate_low` | Amostragem insuficiente. | Usar somente metricas grossas. |
| `noisy` | Sinal precisa filtro/inspecao. | Mostrar warning. |
| `derived` | Canal calculado. | Exportar formula/provenance. |

## Fixture minimo

Cada fixture deve conter:

- `fixture_id`;
- fonte do dado;
- data de criacao;
- veiculo;
- pista;
- formato de entrada;
- mapeamento de canais;
- unidades;
- setup usado;
- solver usado;
- expected output;
- tolerancia;
- status do claim.

## Fixture YAML sugerido

```yaml
fixture_id: interlagos_qss_alpha_001
source: internal_fixture
vehicle_id: porsche_911_gt3_r_992
track_id: interlagos
input:
  file: fixtures/interlagos/session_001.csv
  format: csv
channels:
  speed_mps:
    unit: m/s
    required: true
    aliases: ["speed", "velocity", "Speed"]
  throttle_pct:
    unit: "%"
    required: false
    aliases: ["throttle", "TPS"]
setup:
  wing_position: 5
  tyre_pressure_bar: 1.9
solver:
  name: qss
  engine_version: 0.1.0-alpha
expected:
  lap_time_s:
    min: 92.0
    max: 98.0
claim:
  status: supported
  reviewed_by: vitor
```

## Gate para Sim Reference

Antes de uma Sim Reference aparecer como confiavel:

1. setup precisa estar presente no request e no result;
2. solver e versao precisam estar no result;
3. canais simulados precisam declarar unidades;
4. resultado precisa declarar `confidence_level`;
5. se houver claim fisico, fixture precisa existir;
6. se for 14-DOF, status maximo e `beta` ate CI e runtime estabilizarem.

## Checklist de PR de fisica

- [ ] O PR declara qual claim muda.
- [ ] O PR declara unidade de cada canal/parametro.
- [ ] O PR inclui fixture ou explica por que e refactor sem mudanca fisica.
- [ ] O PR roda teste local.
- [ ] O PR atualiza docs quando muda contrato/canal.
- [ ] O PR nao usa `validated` sem comparacao por canal.

## Template de Physics RFC

```md
# Physics RFC: <titulo>

## Claim

Qual afirmacao tecnica queremos sustentar?

## Motivacao

Por que isso importa para o MVP ou roadmap?

## Dados e fixtures

- Fonte:
- Veiculo:
- Pista:
- Canais:
- Unidades:
- Tolerancias:

## Modelo afetado

QSS, 3-DOF, 14-DOF, tire model, setup model ou ingest?

## Resultado esperado

O que deve mudar em lap time, canal ou tendencia?

## Nivel de claim solicitado

`draft`, `supported` ou `validated`.

## Plano de teste

Comandos e fixtures usados.
```

## Responsabilidades

| Pessoa | Responsabilidade |
|---|---|
| Vitor | Aprovar modelo, fixture, tolerancia e claim. |
| Vinicius | Garantir que produto/landing/demo nao extrapolem o claim. |
| Dev responsavel | Implementar teste, contrato e doc junto do codigo. |
