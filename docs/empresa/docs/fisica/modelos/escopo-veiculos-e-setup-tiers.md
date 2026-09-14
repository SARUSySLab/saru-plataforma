---
titulo: "Escopo de Veículos e Tiers de Setup (LTS)"
data: "2026-08-11"
origem: "_arquivo/saru-app/docs/product/escopo-veiculos-e-setup-tiers.md"
status: "vigente"
area: "produto"
---

# Escopo de Veículos e Tiers de Setup (LTS)

> **Status:** proposta consolidada 2026-07-13 (pré-implementação). SoT de arquitetura segue
> `docs/ARCHITECTURE.md`; física em `saru-core`. Contexto de mercado:
> `docs/research/2026-07-pistas-e-track-days.md`.
> **Problema:** o LTS precisa servir do Onix/HB20/Up! ao 992 GT3 R, com profundidades de
> ajuste MUITO diferentes, sem virar dois produtos.

## 1. O que o LTS responde (por ordem de valor no track day)

1. **"Que tempo esse carro faz nessa pista?"**, volta ideal em condição de track day
   (pneu de rua, grip TD, altitude/temperatura da região) → expectativa realista ANTES do
   evento.
2. **"Onde eu ganho tempo?"**, comparação da volta simulada com a telemetria real (SA), por
   setor/curva.
3. **"O que o ajuste X muda?"**, só para carros/tiers que permitem ajuste (ver §3).

## 2. Estado atual do código (verificado nesta auditoria)

- `vehicles` (Postgres) guarda parâmetros físicos únicos por carro (massa, h_cg, molas,
  ARB, bias, camber/toe, grip, LSD), **sem split dianteira/traseira de mola/amortecedor e
  sem curva de motor/aero** (vivem nos presets do saru-core).
- `lts_setups` (compound, fuel %, asa 0-12, bias %, altura mm, preload Nm) é **exibido na UI
  mas NÃO entra no solver**, `POST /api/v1/lts/run` aceita só `track + vehicle_preset +
  mode`. O painel "Vehicle Params" é decorativo hoje. **Gap nº 1 do LTS.**
- Presets calibrados no saru-core: `porsche_911_gt3_r_992` (oracle ~94s @ Interlagos),
  `mclaren_720s_gt3_default`, `porsche_911_gt3_cup_991`, `truck_diesel_default`. Nenhum carro
  de rua ainda.

## 3. Modelo proposto: 3 tiers de veículo

| | **Tier S, Street** | **Tier P, Performance** | **Tier R, Race/Pro** |
|---|---|---|---|
| Exemplos | Onix, HB20, Up! TSI, Polo | Golf GTI, Civic Si, 718, 911 Carrera, M2 | 911 GT3/GT3 RS, GT3 Cup/R, McLaren GT4/GT3 |
| Fonte de parâmetros | ficha técnica pública (massa, potência, pneu OEM, cx estimado) | ficha técnica + dados de imprensa/dyno | homologação/manual de pista do fabricante |
| Ajustes expostos | **pressão de pneu (psi)** · combustível · piloto (peso) · pneu (OEM/200TW/semi-slick) | + altura (se coilover) · camber (se permitido) · bias (se ajustável) · asa (se houver) | tudo do saru-core: molas/ARB/LSD/aero/bias/alturas |
| Fidelidade declarada | "estimativa de categoria" (±2-3%) | "modelo calibrado quando houver telemetria" | "calibrado vs oracle" (padrão atual) |
| Validação | telemetria de usuários (SA) agrega e recalibra | idem + tempos de referência públicos | oracle oficial (WEC/Cup) |

**Regra de produto:** o tier define o formulário de setup que a UI monta e o que o BFF aceita
em `lts/run`, um Tier S NUNCA mostra campo de ARB; um Tier R mostra tudo. Isso resolve o
"carros de luxo são inacessíveis": no Tier S/P o valor não está no ajuste fino, está na
**expectativa de tempo + coaching de pilotagem**; no Tier R está no **engenheiro de setup**.

## 4. Mudanças de schema (proposta)

```sql
-- vehicles ganha identidade de produto e tier
ALTER TABLE vehicles ADD COLUMN display_name TEXT;      -- "Porsche 911 GT3 R (992)"
ALTER TABLE vehicles ADD COLUMN tier TEXT NOT NULL DEFAULT 'R';  -- 'S' | 'P' | 'R'
ALTER TABLE vehicles ADD COLUMN class TEXT;             -- 'hatch', 'hot-hatch', 'sports', 'gt3'...
ALTER TABLE vehicles ADD COLUMN power_kw REAL;          -- ficha técnica (Tier S/P)
ALTER TABLE vehicles ADD COLUMN drivetrain TEXT;        -- FWD/RWD/AWD
ALTER TABLE vehicles ADD COLUMN tire_spec TEXT;         -- OEM / 200TW / semi-slick
-- setups passam a declarar o que o tier permite (validação no BFF, ADR-0007)
```

- `lts_setups.wing_level 0-12` só faz sentido p/ Tier R, tornar **nullable por tier**.
- Pressão de pneu (psi) entra em `lts_setups`, é O ajuste universal (único que todo track
  day permite, e o que os organizadores já aferem no grid, ver pesquisa §4).

## 5. Roadmap de presets (proposta de sequência)

1. **Validar cadeia com o que existe**: ligar `lts_setups` → `lts/run` (fuel + pressão no
   992 GT3 R). Persistir resultado em `lts_results` (hoje o run "live" não é salvo, Gap nº 2).
2. **Primeiro carro de rua (Tier S)**: 1 hatch popular (ex.: Onix 1.0 turbo) em Interlagos, alvo ~2:05-2:20 (faixa da pesquisa §2), para provar o produto track day.
3. **Tier P**: Golf GTI (âncora pública: 2:10.5 em Interlagos, geração antiga) e um 911.
4. **Pistas**: Interlagos já existe no saru-core; adicionar **Brasília (5.384 m, novo)** e
   **Goiânia (3.835 m)** quando houver traçado confiável (OSM/TUM), com perfil de
   altitude/pressão por pista (§5 da pesquisa).

## 6. Riscos

- **Carros populares sem dados de pneu/inércia** → declarar fidelidade "estimativa" na UI
  (nunca vender precisão que não temos) e recalibrar com telemetria agregada dos usuários.
- **Setup sem efeito no solver** (estado atual) → enquanto §5.1 não fechar, a UI não deve
  sugerir que mudar asa/bias altera o tempo simulado.
- Goiânia: pista fechada p/ recapeamento total (jul→out/2026), presets de grip dela são
  provisórios por definição.
