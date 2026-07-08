# Platform architecture

Reference document. It explains **the connections** between the pieces — the ones
that are not obvious at a glance from the code (structural typing, IoC, lifecycle).
Diagrams first, detail after.

## Table of contents
1. [Overview (Ports & Adapters)](#1-overview-ports--adapters)
2. [Interfaces → implementations](#2-interfaces--implementations)
3. [Initialization sequence](#3-initialization-sequence)
4. [The 3 levels of the factory](#4-the-3-levels-of-the-factory)
5. [yield / context manager / decorator](#5-yield--context-manager--decorator)
6. [Request flow (invoke)](#6-request-flow-invoke)
7. [Where the connections live (structural typing)](#7-where-the-connections-live-protocol-structural-but-made-explicit)
8. [Conventions](#8-conventions)

---

## 1. Overview (Ports & Adapters)

Rule: **the arrows point toward the domain**. The domain (`core`) does not know the
frameworks; adapters depend on the domain, never the reverse.

```
        ADAPTER                          DOMAIN (framework-free)
   ┌──────────────────┐            ┌──────────────────────────────┐
   │ connection/http  │  ──────►   │ core                         │
   │  (FastAPI)       │  depends   │  interface/  (the PORTS)      │
   └──────────────────┘            │  GraphExecutor                │
   ┌──────────────────┐  ──────►   │  GraphRuntimeActivator        │
   │ persistence (DB) │            └──────────────────────────────┘
   └──────────────────┘
                          core ──✗──► adapter   (NEVER)

   tests/  → dev_stub (fake echo provider) + main (dev launcher)
```

| Package | Role | Knows the frameworks? |
|---------|------|----------------------|
| `core` | logic: runs the graphs, defines the ports | ❌ no |
| `connection/http` | exposes the graphs over FastAPI | ✅ yes (FastAPI) |
| `persistence` | DB access | ✅ yes (DB driver) |
| `tests` | fakes + dev launcher | — |

---

## 2. Interfaces → implementations

The **ports** (interfaces) live in `core/interface/`. The **implementations** live in
the package they belong to. The link is made explicit through inheritance
(`class Impl(Interface)`).

```
core/interface/                      implementation (today)        tomorrow
─────────────────────────────────────────────────────────────────────────
GraphRuntimeInterface          ←     EchoGraphRuntime          LangGraphRuntime
GraphProviderInterface         ←     StaticGraphProvider       YamlGraphProvider
ThreadStateInterface           ←     EchoThreadState           StateSnapshot
ConnectionInterface            ←     HttpConnection            CliConnection
GraphProviderFactoryInterface  ←     DevGraphProviderFactory   YamlGraphProviderFactory
```

Naming: implementation = `<Strategy>` + `<interface name without "Interface">`.
E.g. `Echo` + `GraphRuntime` = `EchoGraphRuntime`.

---

## 3. Initialization sequence

Who calls whom, from startup. Note the two moments: **assembly** (cold) and
**start** (FastAPI turns the server on).

```
e2e_tests/user1/PlatformManager.py   (extends AbstractPlatformManager)
   │   asyncio.run(PlatformManager().run())
   ▼
AbstractPlatformManager.run()   (core/platform/)            ◄── deployment INITIATOR
   │   transport = build_transport()                  # HttpTransport(port) — the user's info
   │   activator = GraphRuntimeActivator(build_factory())
   │   provider  = await activator.start()  ──────────┐     # 1) GRAPH up
   │   await transport.serve(provider)                 │     # 2) CHANNEL up = green light
   │   (finally) await activator.stop()                │     # 3) GRAPH down
   ▼                                                   ▼
GraphRuntimeActivator (core/activation/...)   framework-free
   start():  cm = factory.open();  provider = await cm.__aenter__()
   stop():   await cm.__aexit__(...)

HttpTransport.serve(provider)   (connection/http/HttpTransport.py)   ◄── CHANNEL
   │   app = create_app(provider)        # provider ALREADY ready, no lifespan
   │   await uvicorn.Server(Config(app, host, port)).serve()   # serves until shutdown
```

Key point: the initiator is the **PlatformManager** (not a `main`). It brings the
graph up **before** serving the channel (green light); `HttpTransport` receives an
already-ready provider and activates nothing. `create_app` no longer has a lifespan.

---

## 4. The 3 levels of the factory

The factory is an interface with one method:

```python
class GraphProviderFactoryInterface(Protocol):
    def open(self) -> AbstractAsyncContextManager[GraphProviderInterface]: ...
```

From `open()` three **nested levels** unfold:

```
factory   .open()   →   AbstractAsyncContextManager[ GraphProviderInterface ]
└──┬──┘                  └───────────┬────────────┘    └──────────┬──────────┘
LEVEL 1                          LEVEL 2                       LEVEL 3
the factory                    the context manager             the provider
```

| Level | What it is | Concrete object |
|---------|-------|------------------|
| 1 | the factory object (holds the config) | `DevGraphProviderFactory()` |
| 2 | what `open()` **returns** when you call it | `factory.open()` |
| 3 | what the CM **produces** at the `yield` | `StaticGraphProvider` |

```python
class DevGraphProviderFactory(GraphProviderFactoryInterface):  # LEVEL 1
    @asynccontextmanager
    async def open(self):
        yield StaticGraphProvider({...})                       # LEVEL 3: the produced provider

cm = factory.open()                # LEVEL 2: the context manager
provider = await cm.__aenter__()   # LEVEL 3: StaticGraphProvider
```

`StaticGraphProvider` **is** the `GraphProviderInterface` (level 3). The
`AbstractAsyncContextManager` "wrapper" (level 2) is put around it by the
**decorator**: it belongs to `factory.open()`, not to the provider.

---

## 5. yield / context manager / decorator

`open()` is a generator method. Three states to distinguish:

```
1)  factory               → I pass the factory OBJECT — nothing in open runs yet
2)  factory.open()        → I create the CONTEXT MANAGER (the decorator) — body STILL frozen
3)  await cm.__aenter__() → I RUN open's body up to the yield → I get the provider
```

The `yield` cuts the method in two:

```
   async def open(self):
       <opening>           ┐
       yield provider      ┘ ← __aenter__ runs up to HERE  (1st next)
       <closing>           ← __aexit__ runs from HERE on   (2nd next)
```

**What `@asynccontextmanager` is for:** it turns the generator into a context
manager, fabricating `__aenter__`/`__aexit__`. Without it, you would have to drive the
generator by hand with `anext`, and handle yourself:
- `StopAsyncIteration` (the 2nd `anext` raises it when the generator ends);
- **error propagation** inside the generator (so the closing code runs even on an
  exception).

The decorator does all of this for you and gives the standard `async with` interface.

---

## 6. Request flow (invoke)

IoC in action: channel and executor created **per-request**, dependencies injected as
interfaces.

```
POST /graphs/demo/invoke
   │
   ▼
routes/graphs_router.py  → invoke()
   │   channel  = HttpConnection()                 (implements ConnectionInterface)
   │   executor = GraphExecutor(graph, channel)    (IoC: receives the INTERFACES)
   ▼
GraphExecutor.run(input, thread_id)   (core)
   │   result = await graph.ainvoke(...)           (via GraphRuntimeInterface)
   │   await channel.send(result)                  (via ConnectionInterface)
   ▼
the route returns  channel.payload   →   HTTP response
```

`GraphExecutor` calls **only interface methods**: it does not know that `graph` is an
`EchoGraphRuntime` nor that `channel` is FastAPI. Both are swappable without touching it.

---

## 7. Where the connections live (Protocol: structural, but made explicit)

`Protocol`s are **structural**: an object satisfies the interface if it has the right
methods, even without inheriting it. That is why there are two different "readers":

- **At runtime**: nobody checks anything. Python does **duck typing**: it calls the
  method and it works if the object behaves; otherwise it breaks *on first use*.
- **At type-check time** (mypy/pyright): conformance is verified by **structure**, at
  the point where you pass the object to a parameter typed with the interface.

In this project, however, we choose to make the link **explicit**: every
implementation **inherits** the interface (`class HttpConnection(ConnectionInterface)`).
It is not mandatory for `Protocol`s, but:
- the link is **visible** in the class name (like `implements` in Java);
- the type checker **verifies** the methods are actually there (error if `send` is missing).

```
class DevGraphProviderFactory(GraphProviderFactoryInterface):   # ← EXPLICIT link
    async def open(self): ...
```

Historical note: the factory was originally a **`Callable` alias** — no implementer,
link only structural at the point of use. We promoted it to
`GraphProviderFactoryInterface` with the `DevGraphProviderFactory` class that inherits
it, precisely to remove that exception and have the same pattern everywhere.

---

## 8. Conventions

- **Interfaces**: `typing.Protocol`, `Interface` suffix; implementations **inherit**
  explicitly (`class HttpConnection(ConnectionInterface)`).
- **One class per file**, file = class name in **CamelCase** (`GraphExecutor.py`).
- **Function-only modules** → `snake_case` (`app.py`, `graphs_router.py`).
- **Implementation naming** = `<Strategy><Interface>` (`EchoGraphRuntime`).
- **DTOs per adapter** (HTTP bodies live in `connection/http/DTO/`, not in core).
- **Imports**: relative within the same package, absolute across boundaries.
- **IoC**: dependencies are **injected** as interfaces; only the *composition root*
  (entrypoint, factory, per-request route) knows the concrete classes.
