# AP-14 probe — banco di prova manuale

Verifica a mano AP-14 (recupero stato / `StateHistory` + nodi `ctx-first`), su un
grafo **senza LLM** così gira deterministico e senza chiavi.

```
START -> probe -> (LoopRouter) -> probe | END        # 3 giri, poi END
```

`CounterProbe` (L0) a ogni giro legge la storia del thread **da dentro il nodo** e
scrive l'evidenza nel bag `execution_data` (quindi la si vede da HTTP).

## Come si esegue

Shell 1 — server (nessun `.env` necessario):
```
cd e2e_tests/ap14_probe
uv run python PlatformManager.py
```

Shell 2 — driver curl (serve `jq`):
```
cd e2e_tests/ap14_probe
bash ap14_curls.sh          # usa il thread "t1"; passa t2/t3 per ripartire pulito
```

## Cosa guardare

**Parte B — `ctx.history` / `ctx.previous` IN-NODO** (passo 1, `include_state`):
in `execution_data` compaiono, per ogni giro `N` (N = il contatore in ingresso, 0/1/2):
- `stepN_num_checkpoints` — deve **crescere** (qui 2, 3, 4). Se restasse 0, vorrebbe
  dire che si sta leggendo il motore (vuoto mid-run) invece del checkpointer: è
  esattamente il bug che AP-14 risolve. **È la prova più diretta.**
- `stepN_back0_count` vs `stepN_back1_count` — `ctx.history.back(0)` (il tuo input) e
  `back(1)` (un super-step prima). Qui vengono `back0 = null, 1, 2` e
  `back1 = null, null, 1`: back(1) è sempre "uno indietro" rispetto a back(0) → la
  scala `back(n)` funziona.
- `stepN_prev_count` — `ctx.previous` (no `await`) **coincide con `back(1)`**
  (`null, null, 1`). Esce `null` finché il contatore non esiste ancora nei checkpoint
  più vecchi: compare solo dopo il 1° giro, quindi `back(1)` lo "vede" dal 3° giro.
  Off-by-one atteso, non un bug.
- (`stepN_back1 = "ROOT"` apparirebbe solo se `back(1)` superasse l'inizio della
  storia; qui c'è sempre un checkpoint iniziale, quindi non scatta.)

**Parte A — route HTTP** (passi 3–7):
- `/state/history` → l'indice dei checkpoint (dal più recente).
- `/state/previous` → lo stato del super-step precedente.
- `/state/at/{id}` → lo stato a un checkpoint preciso.
- `/state/at/BOGUS` → **404**; e lo stesso id su un thread diverso → **404**
  (isolamento per-thread: nessun leak cross-thread).

> Nota: con il checkpointer in-memory la storia vive per la durata del processo.
> Riavviando il server si riparte da zero.
