# Handoff — build the visualizer (a new session)

Goal: a **GPU-accelerated, progressively-rendering dashboard** that **drives the demo CLI** and
renders the resulting `scene/v0.1`. The dashboard is the control surface (pick a question, scrub a
knob, toggle guided/open); the demo is the compute backend; the scene JSON is the wire between
them. The visualizer runs **no physics** — it renders computed, gate-vetted data.

Read first: [`architecture_scene_visualizer.md`](architecture_scene_visualizer.md) (the full
design) and [`fake_nan_discipline.md`](fake_nan_discipline.md) (why every value carries a verdict).
Develop against the frozen [`../fixtures/scene_all.json`](../fixtures/scene_all.json) before wiring
the CLI — you can build the entire renderer with no Python running.

---

## 1. What you are handed

- **The contract** — `scene/v0.1`, defined as frozen dataclasses in
  [`../demo/scene_contract.py`](../demo/scene_contract.py). Mirror these fields in the
  visualizer's types. A `Scene` is `{ meta, axes[], views[], provenance }`:
  - `meta`: `title`, `framing[]` (disclaimers you MUST surface), `mode_default` (`"guided"`),
    `modes` (`["guided","open"]`), `guided[]` (ordered tour steps).
  - `axes[]`: `{ name, label, values[] }` — **pre-swept** parameter dimensions → one slider each.
  - `views[]`: typed panels (table below).
  - Every graded datum is a **Channel** `{ value | values[], over[], unit, verdict, role, label }`.
- **The CLI** — `python demo/character_scene.py --explore {minting,drive,ledgers,boundary,cascade,all} --emit <path>`.
- **The fixture** — `fixtures/scene_all.json`, a full `--explore all` scene to render offline.

## 2. Interaction model (dashboard ↔ CLI)

```
  dashboard controls ──▶  invoke `character_scene.py --explore … [--cascade-depth d] --emit scene.json`
   (explore picker,        ▲                                                              │
    axis sliders,          │  (re-run only when a STRUCTURAL input changes:               ▼
    guided/open toggle)    │   which explorations, cascade depth, refine factor)     scene/v0.1 JSON
                           └──────────────────────────────────────────────────────  load + render
```

Key distinction that keeps it fast:
- **Axis scrubbing needs NO recompute.** Axes are pre-swept; a channel indexed `over:["drive"]`
  already carries its value at every sampled drive. Moving a slider just indexes the arrays.
- **Only structural changes re-invoke the CLI** — choosing different `--explore` questions,
  changing `--cascade-depth`, or raising the refine factor for a sharper gate. Debounce these and
  show a "recomputing…" state; everything else is instant.

A thin local bridge runs the CLI on demand (see stack options). The dashboard never imports the
physics; it shells out and reads JSON.

## 3. The stack (decided — optimize for growth, not current load)

The compute→scene→render split already lets compute and rendering scale independently. The
renderer is the one subsystem expected to grow 10×+ (graph size, fields, refinement), so it gets a
real engine; everything else stays thin.

| layer | choice |
|---|---|
| UI / controls | React or Svelte — sliders, toggles, the guided-tour overlay |
| scene model | **TypeScript**, mirroring `scene_contract.py`'s dataclasses 1:1 |
| renderer | **WebGPU** — GPU-resident geometry, uniform-driven interaction, accumulation for progressive refinement |
| bridge | **FastAPI** — ~30 lines, `POST /scene` runs `character_scene.py … --emit` and returns JSON |
| compute | the Python CLI, **entirely outside the visualization process** |

WebGPU from day one — not WebGL-then-port. On this hardware it drives the GPU as fully as any
native path (browser → D3D12/Vulkan), so there is no GPU-utilization reason to go native.

**Not Taichi.** Taichi earns its keep when the renderer *is* the simulation. This architecture
forbids that — the renderer runs no physics, the simulation already happened, you are visualizing
vetted outputs. That single rule removes Taichi's reason to exist here. (PyQt + moderngl is a
viable native fallback only if a browser is ever off the table; it is not the default.)

## 3a. Designing for 10× growth

The project is research-oriented: graph size will go 10²→10⁴, scalars will become *fields*
(circulation, uncertainty, flow), and a new `view kind` will appear every few months. Build so
that growth is cheap.

- **GPU-resident geometry; interaction is uniforms — for *value* axes.** Upload nodes / edges /
  positions once; scrubbing `drive` / `time` / `toward_edge` updates *uniforms*, not meshes — no
  DOM churn, no chart rebuild. **Caveat:** *structural* axes (`n_nodes` 2→3, `cascade_depth` 1→d)
  change the geometry itself → re-upload, or pre-load all variants and switch. Design for two
  classes of axis: value-axes = uniforms, structural-axes = geometry. Don't assume geometry is
  immutable.
- **Composable primitives — not a widget zoo, and not a speculative engine.** One failure mode is
  a custom widget per view kind; the opposite is a generic scene-graph + shader-compiler you build
  for view kinds that don't exist yet. Sit in the middle: a small library of GPU **primitives** —
  instanced points, instanced lines, line-strips, a **field/texture pass**, a text/annotation
  layer — that view kinds *compose*. `graph` = points + lines + labels; a future
  `protection_landscape` = field pass + contour lines. A new view kind is a new *composition +
  data binding*, not a new shader and not a new widget. (Grammar-of-graphics at the GPU level:
  most "new views" are recombinations of marks + fields + annotations.)
- **Progressive refinement is end-to-end, not a render trick.** The first wall is *compute*, not
  the GPU. A monolithic scene emit — *doubled by the gate's base + refine×* — is what balloons at
  10⁴ nodes / deep cascades / fine sweeps, long before the 4080 sweats. So the contract should grow
  to **stream**: static geometry first (instant preview) → coarse channels → refined channels.
  "Low fidelity first, then refine" then runs from compute to pixel, one accumulation buffer
  serving both. This is a `scene/v0.x` evolution (partial / patch scenes) and it matters more than
  any renderer choice. **Likely the first thing you'll actually need.**
- **Forward-compatible by default.** A renderer **skips unknown view kinds** (and surfaces them),
  never crashes. Pin the major schema version; tolerate unknown minors. Evolution stays additive;
  an old renderer degrades gracefully against a newer scene.

## 4. Progressive rendering (what it means here)

Two layers, both "coarse first, then refine":
- **Visual** — draw each view immediately at low fidelity (few samples / low-res passes), then
  accumulate to high fidelity over frames while idle (the high-quality viewing floor still applies:
  4K target, 2K minimum once settled). Natural in WebGPU via accumulate-over-frames.
- **Data** — the demo's convergence gate has a `--refine`-style knob (base vs refine× resolution).
  A "sharpen" action can re-invoke the CLI at higher refinement; channels whose `verdict` was
  borderline tighten. Show the verdict changing as it sharpens. At scale this becomes the
  **streaming** path in §3a (geometry → coarse channels → refined channels), so the same coarse→
  fine motion runs end-to-end, compute through pixel.

## 5. View → visual mapping

| view `kind` | data it carries | suggested rendering |
|---|---|---|
| `graph` | `nodes`, `edges{from,to,sign,reciprocal}`, `layout[]`, a `circulation` channel over an axis | node-link on the layout; animate a circulating flow whose speed/width ∝ the circulation channel; sign = edge color |
| `series` | `x`, `traces[]{name,y[]}`, `markers[]{x,label}` | multi-trace line plot; vertical event markers (e.g. "drive ramp starts") |
| `locus` | parametric `points[[x,y]]`, reference channels (`X_eq`, `X_aging`) | scatter/line in the (x,y) plane; draw the slope-1 and slope-X reference branches |
| `spectrum` | `before[[re,im]]`, `after[[re,im]]` | complex-plane points; highlight the emergent conjugate pair |
| `hierarchy` | `levels[]{k,rate,eps,sigma,role}`, totals | a stacked tower; per-level σ; up-climb / down-cost arrows; mark the ε→1 cutoff |
| `sweep` | `x`, channels over the axis, a `boundary{at,label}` | curve(s) vs the control; render the `boundary` marker as an unreachable wall |
| `readout` | named scalar channels with `unit`, `verdict` | a panel of labelled numbers; style by verdict (below) |
| `field` *(planned, scene/v0.2)* | a sampled grid / texture-backed channel (circulation as a vector field, an uncertainty field) | the field/texture pass — GPU-native; the reason to include a field primitive from day one |

## 6. Honor the verdict (non-negotiable, and general)

`Channel.verdict ∈ {analytic, converged, boundary_tripwire, unconverged, fake_nan_cleared}`.

- `analytic` / `converged` → render as fact.
- `boundary_tripwire` (value arrives as `null`) → render as a distinguished **edge-state**, not a
  number. In the `boundary` view this is the *answer* to "what's at the extreme?".
- `unconverged` / `fake_nan_cleared` → do **not** render as fact; mark as not-yet-trustworthy.

This rule is part of the *general* apparatus — any future scene source relies on it, not just
character.

## 7. Guided (default) and open (toggle)

`meta.mode_default` is `"guided"` — **start here, because a lost learner gives up.**
- **Guided** — walk `meta.guided[]` in order (`q1…q5`): focus the named `view`, surface the named
  `axis`, show the `prompt` ("turn the drive down to 0 — watch the circulation vanish"). One step
  at a time, Next/Back.
- **Open** — all views and axes available to roam freely. A visible toggle switches modes; default
  to guided on first load.

Also surface `meta.framing[]` persistently (the "illustration, not evidence" / "calibration, not a
test" lines) — it must not be dismissable away to nothing.

## 8. Start here

1. Render `fixtures/scene_all.json` statically — all 8 views, 4 axes, 5 guided steps — with no
   backend. Get the View vocabulary and verdict styling right first.
2. Add axis sliders (pure indexing into pre-swept channels).
3. Add the guided/open toggle and the guided walkthrough.
4. Only then add the bridge so `--explore` / `--cascade-depth` re-invoke the CLI.
5. Layer in progressive rendering once the static picture is correct.

## 9. Open decisions for your session

Stack is decided (§3). What's left:
1. **Bridge transport** — local HTTP server, or a one-shot subprocess per recompute, or a
   long-lived stdio worker. (HTTP is simplest; stdio is lowest-latency; the streaming path in §3a
   wants a persistent channel, so a long-lived stdio/websocket worker is the growth-friendly pick.)
2. **Scene caching** — cache emitted scenes by `(explore set, depth, refine)` so re-selecting a
   prior configuration is instant.
3. **When to add `field` + streaming** — not for the first cut (the discrete views + the fixture
   are enough to get a working dashboard). Add them when graph size or field-shaped observables
   actually arrive; build the primitive set so the field pass slots in without a rewrite.
