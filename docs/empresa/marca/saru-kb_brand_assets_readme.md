---
titulo: "Brand Assets, depósito de logo/imagens do saruê"
data: "2026-07-15"
origem: "_arquivo/saru-KB/50_company/brand_assets/README.md"
status: "vigente"
area: "marca"
---

# Brand Assets, depósito de logo/imagens do saruê

**Coloque aqui** os arquivos do logo e variações. O agente lê esta pasta p/ gerar opções de cor,
extrair #HEX e subir no Canva Brand Kit (deck).

## Formato (ordem de preferência)

1. **SVG** (`sarue-logo-master.svg`), melhor: agente lê/edita como código → recolore, gera variações
   #HEX direto, escala sem perda. Se o desenho nasceu vetorial (Figma/Illustrator/Inkscape), exportar SVG.
2. **PNG transparente** na maior resolução disponível (≥1000 px lado maior), se o esboço é raster
   (desenho/IA). Agente lê visualmente, extrai paleta e propõe #HEX, mas não edita o vetor.
3. Evitar: JPG (fundo chapado, artefato), PDF de página inteira, screenshot comprimido.

## Naming

`sarue-logo-master.svg` · `sarue-logo-<variante>.svg|png` (ex.: `dark`, `light`, `mono`, `albino-v2`)

## Fluxo combinado (2026-07-15)

1. Vitor dropa esboço/variações aqui.
2. Agente gera opções de cor em SVG + tabela de #HEX candidatos.
3. Vitor escolhe → #HEX finais registrados no [`SARU_BRAND_DNA.md`](../SARU_BRAND_DNA.md) §1.
4. Upload no Canva Brand Kit → deck (módulo 10 §4) destravado.
