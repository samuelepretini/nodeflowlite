# Test E2E [AP-18] — istruzioni operative

Test end-to-end dell'intero framework **come lo vivrebbe un utente finale**:
installazione da repo privato, risoluzione delle dipendenze, scaffold del progetto e
un primo **test case** che esercita i **quattro livelli di nodo** della scala di
controllo + il recupero della **storia dello stato (AP-14)**, su un **workflow lineare
senza router**.

> Il tester parte **da zero**. Tutto ciò che segue va eseguito in una cartella **esterna**
> al repo del framework (simuliamo un consumatore reale che installa `agent_platform`
> come dipendenza). Questo documento è l'unica cosa che vive dentro il repo.

---

## 1. Cosa validiamo

- **Installazione utente**: il framework si installa da git come dipendenza e lo scaffold
  genera un progetto eseguibile.
- **I quattro livelli di nodo** in un solo grafo lineare:
  - **L0** `AbstractNode` — nodo pure-Python, niente LLM (`run(ctx)` + `ctx.state.set_data`).
  - **L1** `AbstractCommonNode` — agente solo-config (`MODEL`/`SYSTEM_PROMPT`/`TOOLS`).
  - **L2** `AbstractHookedNode` — hook `before_invoke`/`after_invoke`/`on_error`.
  - **L3** `AbstractCommonNode` + override — `build_prompt` (input) e `on_result` (output).
- **AP-14 — storia dello stato**:
  - **da dentro un nodo**: l'ultimo nodo (L0) legge gli stati dei super-step precedenti
    con `await ctx.history.back(n)` — senza mai vedere un `thread_id`.
  - **da fuori (HTTP)**: gli endpoint `/state`, `/state/previous`, `/state/history`,
    `/state/at/{checkpoint_id}`.
- **Workflow lineare**: `START → describe → restyle → annotate → collect → END`. Nessun
  router, nessun ciclo (i router sono fuori scope per questo primo caso).

> Riferimenti: [`docs/manuale-operativo.md`](../../docs/manuale-operativo.md) (installazione,
> esecuzione, output) e [`docs/ap14-state-history.md`](../../docs/ap14-state-history.md)
> (la history).

---

## 2. Prerequisiti

- **Python ≥ 3.11** e **[uv](https://docs.astral.sh/uv/)**.
- Una **API key OpenRouter** (3 dei 4 nodi sono LLM).
- Accesso SSH al repo privato. Su questa macchina l'host alias è **`github-samuele`**
  (verifica: `ssh -T git@github-samuele` deve rispondere `Hi samuelepretini!`).

---

## 3. Installazione (come utente finale, in cartella ESTERNA)

```bash
# 1. cartella nuova, FUORI dal repo del framework
mkdir -p ~/ap18-usertest && cd ~/ap18-usertest

# 2. progetto uv vergine
uv init

# 3. installa il framework dal repo privato (host SSH personale)
uv add "git+ssh://git@github-samuele/samuelepretini/AgenticPlatform.git"

# 4. il progetto utente legge il .env: serve python-dotenv
uv add python-dotenv

# 5. genera lo scaffold nella cartella corrente (nome progetto = AP18Test)
uv run python -m agent_platform.scaffold . AP18Test
```

Lo scaffold scrive `agents/`, `routers/`, `tools/`, `graphs/MyGraph.yaml`,
`PlatformManager.py`, `.env.example`, `README.md`. **Non sovrascrive** file esistenti.

Poi la chiave:

```bash
cp .env.example .env
# apri .env e metti:  OPENROUTER_API_KEY=sk-or-v1-...
```

> **Smoke test prima di toccare il codice**: `uv run python PlatformManager.py` deve
> avviare il server su `http://localhost:8000` servendo il grafo `MyGraph` di default
> (START → worker → END). Fermalo (Ctrl-C) e procedi a sostituire i contenuti.

---

## 4. Il test case — pipeline lineare a 4 nodi

Riempiamo i **quattro stub** già generati (teniamo i nomi-classe dello scaffold, così il
registry nel `PlatformManager.py` resta invariato) e riscriviamo il grafo. Tema banale e
verificabile: *descrivi un topic → riscrivilo in uno stile → annotalo → raccogli la
storia del run*.

### 4.1 Il grafo — `graphs/MyGraph.yaml`

Sostituisci **tutto** il contenuto del file con:

```yaml
name: MyGraph
description: Linear pipeline exercising the four node levels + AP-14 state history.
version: 1

# execution_data is auto-injected by the builder — no need to declare it.
state:
  messages: { type: list, reducer: add_messages }

nodes:
  describe: { agent: BasicWorker }    # L1 — config-only
  restyle:  { agent: ShapingWorker }  # L3 — build_prompt + on_result
  annotate: { agent: HookedWorker }   # L2 — before/after hooks
  collect:  { agent: CounterNode }    # L0 — reads the state history (AP-14)

edges:
  - { from: START,    to: describe }
  - { from: describe, to: restyle }
  - { from: restyle,  to: annotate }
  - { from: annotate, to: collect }
  - { from: collect,  to: END }
```

### 4.2 L1 — `agents/BasicWorker.py`

Solo configurazione, nessun metodo:

```python
from __future__ import annotations

from agent_platform.core.abstract.AbstractCommonNode import AbstractCommonNode


class BasicWorker(AbstractCommonNode):
    MODEL = "openai/gpt-4o-mini"        # CHOICE: any OpenRouter model
    SYSTEM_PROMPT = "You are concise. In ONE sentence, describe the topic the user gives you."
    TOOLS = []
```

### 4.3 L3 — `agents/ShapingWorker.py`

Modella l'input (`build_prompt`) e l'output (`on_result`):

```python
from __future__ import annotations

from agent_platform.core.abstract.AbstractCommonNode import AbstractCommonNode
from agent_platform.core.interface.StateInterface import StateInterface
from agent_platform.core.state.NodeContext import NodeContext


class ShapingWorker(AbstractCommonNode):
    MODEL = "openai/gpt-4o-mini"
    SYSTEM_PROMPT = "You rewrite text. Keep it to a single sentence."
    TOOLS = []

    def build_prompt(self, state: StateInterface) -> str:
        # INPUT shaping (sync, strings only): the previous node's answer is the prompt;
        # the style comes from execution_data (seeded from the invoke input, default below).
        text = state.last_message_content
        style = state.execution_data.get("style", "formal")
        return f"Rewrite the following in a {style} style:\n{text}"

    def on_result(self, ctx: NodeContext, result: StateInterface):
        # OUTPUT shaping (sync): record the styled text in the bag, then RETURN the
        # message (the framework emits it — no reply, no return of the channel).
        ctx.state.set_data("styled", result.last_message_content)
        return result.last_message
```

### 4.4 L2 — `agents/HookedWorker.py`

Hook attorno alla chiamata LLM:

```python
from __future__ import annotations

from typing import Any, Mapping

from langchain_core.messages import BaseMessage

from agent_platform.core.abstract.AbstractHookedNode import AbstractHookedNode
from agent_platform.core.interface.StateInterface import StateInterface
from agent_platform.core.state.NodeContext import NodeContext


class HookedWorker(AbstractHookedNode):
    MODEL = "openai/gpt-4o-mini"
    SYSTEM_PROMPT = "Prepend a short emoji title line, then repeat the text you receive."
    TOOLS = []

    async def before_invoke(self, ctx: NodeContext) -> Mapping[str, Any]:
        # Pre-hook (INPUT): record how many messages we saw via ctx.state.set_data (the
        # framework collects it). Return {} = no change to what the model sees.
        ctx.state.set_data("hook_seen_messages", len(ctx.state.messages))
        return {}

    async def after_invoke(
        self, ctx: NodeContext, result: StateInterface
    ) -> "str | BaseMessage | None":
        # Post-hook (OUTPUT): enrich execution_data via ctx.state, then RETURN the
        # model's message (the framework emits it).
        ctx.state.set_data("annotated", True)
        return result.last_message
```

### 4.5 L0 — `agents/CounterNode.py` (il lettore della history, AP-14)

Nodo pure-Python, **ultimo** della catena: legge gli stati dei super-step precedenti.

```python
from __future__ import annotations

from agent_platform.core.abstract.AbstractNode import AbstractNode
from agent_platform.core.state.NodeContext import NodeContext


class CounterNode(AbstractNode):
    async def run(self, ctx: NodeContext) -> None:
        # AP-14: read PREVIOUS super-steps of THIS thread — no thread_id here, history is
        # already bound to the running thread. back(0) ≈ now, back(1) one step back, etc.
        prev1 = await ctx.history.back(1)
        prev2 = await ctx.history.back(2)
        last1 = prev1.last_message
        ctx.state.set_data("history_report", {
            "back1_messages": len(prev1.messages),
            "back2_messages": len(prev2.messages),
            "back1_last": last1.content[:80] if last1 else None,
            "back1_styled": prev1.execution_data.get("styled"),
        })
```

> **Cosa stiamo validando qui**: che `back(n)` funzioni **da dentro un nodo, mid-run**
> (legge dal checkpointer, non dal motore). Atteso: `back1_messages` e `back2_messages`
> sono **diversi** (la catena messaggi cresce passo dopo passo) e `back1_styled` mostra il
> testo scritto da `ShapingWorker` due nodi prima — prova che `execution_data` viaggia
> nella storia. Alternativa documentata per i checkpoint espliciti: `ctx.history.checkpoints()`
> + `ctx.history.at(checkpoint_id)`; per il solo passo precedente in codice sync,
> `LOAD_PREVIOUS = True` + `ctx.previous`.

> **Nota registry**: `PlatformManager.py` (generato dallo scaffold) mappa già
> `BasicWorker`/`ShapingWorker`/`HookedWorker`/`CounterNode`. Non va modificato.

---

## 5. Esecuzione e invocazione

```bash
uv run python PlatformManager.py        # → http://localhost:8000
```

In un altro terminale, invoca passando il **topic** e seminando lo **stile** in
`execution_data`:

```bash
curl -s http://localhost:8000/graphs/MyGraph/invoke \
  -H "Content-Type: application/json" \
  -d '{
        "thread_id": "ap18-1",
        "input": {
          "messages": [{"role": "user", "content": "the Moon"}],
          "execution_data": {"style": "ironic"}
        },
        "include_state": true
      }' | python -m json.tool
```

Nella risposta (`include_state: true`) controlla **`state.execution_data`** — deve contenere:

| Chiave | Scritta da | Atteso |
|---|---|---|
| `styled` | `ShapingWorker` (L3, `on_result`) | il testo riscritto |
| `hook_seen_messages` | `HookedWorker` (L2, `before_invoke`) | un intero > 0 |
| `annotated` | `HookedWorker` (L2, `after_invoke`) | `true` |
| `history_report` | `CounterNode` (L0, AP-14) | dict con i 4 campi, `back1_styled` valorizzato |

---

## 6. Verifica AP-14 dall'esterno (HTTP)

Stesso `thread_id` usato sopra (`ap18-1`):

```bash
# stato persistito corrente (values + next)
curl -s http://localhost:8000/graphs/MyGraph/threads/ap18-1/state | python -m json.tool

# indice dei checkpoint (id, nodo, step, timestamp) — dal più recente
curl -s "http://localhost:8000/graphs/MyGraph/threads/ap18-1/state/history?limit=20" | python -m json.tool

# stato di uno step prima
curl -s http://localhost:8000/graphs/MyGraph/threads/ap18-1/state/previous | python -m json.tool

# stato a un checkpoint preciso (prendi un checkpoint_id dall'indice qui sopra)
curl -s http://localhost:8000/graphs/MyGraph/threads/ap18-1/state/at/<CHECKPOINT_ID> | python -m json.tool
```

Atteso: `history` elenca più checkpoint con la **label del nodo** (`describe`/`restyle`/
`annotate`/`collect`); `at/<id>` restituisce lo stato di quel super-step; un
`checkpoint_id` inesistente → **404**.

---

## 7. Acceptance (checklist)

- [ ] Lo scaffold si installa e gira out-of-the-box (smoke test passato).
- [ ] Il grafo lineare a 4 nodi esegue senza errori (`200` su `invoke`).
- [ ] **L1** produce una descrizione; **L3** la riscrive nello stile richiesto
      (`styled` valorizzato); **L2** scrive `hook_seen_messages` (before) e `annotated`
      (after); **L0** scrive `history_report`.
- [ ] **AP-14 in-nodo**: `history_report.back1_messages ≠ back2_messages` e
      `back1_styled` contiene il testo di `ShapingWorker`.
- [ ] **AP-14 HTTP**: `/state`, `/state/previous`, `/state/history` rispondono;
      `/state/at/<id valido>` → stato; `/state/at/<id inesistente>` → 404.

> Annota ogni scostamento (errore, campo mancante, comportamento inatteso): è esattamente
> ciò che questo E2E deve far emergere.
