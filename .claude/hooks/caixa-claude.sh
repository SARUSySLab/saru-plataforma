#!/usr/bin/env bash
# UserPromptSubmit: injeta no contexto as respostas R<n> novas do Antigravity em docs/handoff/caixa-claude.md.
# Estado (último R visto) em .claude/.estado-caixa, fora do git. CAIXA_ESTADO sobrepõe, para teste.
raiz="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
caixa="$raiz/docs/handoff/caixa-claude.md"; estado="${CAIXA_ESTADO:-$raiz/.claude/.estado-caixa}"
[ -f "$caixa" ] || exit 0
ultimo=$(cat "$estado" 2>/dev/null); ultimo=${ultimo:-0}
atual=$(grep -c '^## R' "$caixa")
[ "$atual" -gt "$ultimo" ] || exit 0
echo "$atual" > "$estado"
printf 'Respostas novas do Antigravity em docs/handoff/caixa-claude.md (R%d a R%d), lidas pelo hook:\n\n' "$((ultimo+1))" "$atual"
awk -v pular="$ultimo" '/^## R/{n++} n>pular' "$caixa"
