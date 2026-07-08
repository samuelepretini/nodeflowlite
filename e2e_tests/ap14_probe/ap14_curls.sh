#!/usr/bin/env bash
#
# AP-14 manual test driver (curl).
#
# 1) In one shell, start the server:
#       cd e2e_tests/ap14_probe && uv run python PlatformManager.py
# 2) In another shell:
#       cd e2e_tests/ap14_probe && bash ap14_curls.sh
#
# Needs `jq` for pretty-printing and to pull a checkpoint id (brew install jq).
# Drop the `| jq .` pipes if you don't have it.

set -euo pipefail

BASE="${BASE:-http://localhost:8000}"
G="HistoryProbe"
T="${1:-t1}"   # thread id (pass a fresh one to start from scratch)

hr() { printf '\n=== %s ===\n' "$1"; }

hr "0) grafi serviti  (atteso: [\"HistoryProbe\"])"
curl -s "$BASE/graphs" | jq .

hr "1) INVOKE — esegue il loop; include_state mostra execution_data  [PARTE B: in-nodo]"
# Guarda i campi stepN_num_checkpoints (devono CRESCERE: 0/1/2…), stepN_prev_count
# (compare dal 2o giro) e stepN_back1*: è la prova che ctx.history/ctx.previous
# funzionano DA DENTRO il nodo.
curl -s -X POST "$BASE/graphs/$G/invoke" \
  -H "Content-Type: application/json" \
  -d "{\"thread_id\":\"$T\",\"input\":{},\"include_state\":true}" | jq .

hr "2) /state  — stato corrente + 'next'  (a fine run next è vuoto)"
curl -s "$BASE/graphs/$G/threads/$T/state" | jq .

hr "3) /state/history — indice dei checkpoint, dal più recente  [PARTE A]"
curl -s "$BASE/graphs/$G/threads/$T/state/history" | jq .

hr "4) /state/previous — lo stato del super-step precedente  [PARTE A]"
curl -s "$BASE/graphs/$G/threads/$T/state/previous" | jq .

hr "5) /state/at/{id} — stato a un checkpoint preciso (id preso dalla history)  [PARTE A]"
CID=$(curl -s "$BASE/graphs/$G/threads/$T/state/history" | jq -r '.checkpoints[1].checkpoint_id')
echo "checkpoint scelto (history[1]): $CID"
curl -s "$BASE/graphs/$G/threads/$T/state/at/$CID" | jq .

hr "6) /state/at/BOGUS — checkpoint inesistente  (atteso: HTTP 404)"
curl -s -o /dev/null -w "HTTP %{http_code}\n" \
  "$BASE/graphs/$G/threads/$T/state/at/does-not-exist"

hr "7) /state/at/{id} su un THREAD diverso — isolamento per-thread  (atteso: HTTP 404)"
curl -s -o /dev/null -w "HTTP %{http_code}\n" \
  "$BASE/graphs/$G/threads/altro-thread/state/at/$CID"

printf '\nFatto. Rilancia con un thread nuovo per ripartire pulito:  bash ap14_curls.sh t2\n'
