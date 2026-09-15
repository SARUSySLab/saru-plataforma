#!/usr/bin/env bash
# PreInvocation do Antigravity: injeta as mensagens M<n> novas de docs/handoff/caixa-antigravity.md como userMessage.
# Estado em .agents/.estado-caixa, fora do git. Primeiro teste do formato injectSteps (2026-09-14).
raiz="$(cd "$(dirname "$0")/../.." && pwd)"
caixa="$raiz/docs/handoff/caixa-antigravity.md"; estado="${CAIXA_ESTADO:-$raiz/.agents/.estado-caixa}"
[ -f "$caixa" ] || { echo '{}'; exit 0; }
ultimo=$(cat "$estado" 2>/dev/null); ultimo=${ultimo:-0}
atual=$(grep -c '^## M' "$caixa")
[ "$atual" -gt "$ultimo" ] || { echo '{}'; exit 0; }
echo "$atual" > "$estado"
texto=$(awk -v pular="$ultimo" '/^## M/{n++} n>pular' "$caixa")
python3 -c 'import json,sys; print(json.dumps({"injectSteps":[{"userMessage":"Mensagens novas do Claude Code em docs/handoff/caixa-antigravity.md. Responda em docs/handoff/caixa-claude.md com o mesmo numero.\n\n"+sys.stdin.read()}]}, ensure_ascii=False))' <<< "$texto"
