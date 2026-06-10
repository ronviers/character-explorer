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

## 3. Recommended stack

**Recommendation: a web dashboard + WebGPU renderer + a thin Python bridge.**
- *Dashboard / controls* — web UI (your choice of vanilla/Svelte/React). Dashboards are strongest
  in the browser; sliders, toggles, and a guided-tour overlay are native there.
- *GPU progressive rendering* — **WebGPU** (WebGL2/regl/Three.js as a fallback). The 2026-modern
  GPU path; integrates with a web dashboard with no native build.
- *Bridge* — a ~30-line local server (FastAPI/Flask) exposing `POST /scene` that runs
  `character_scene.py --explore … --emit` and returns the JSON. Keeps the dashboard physics-free.

Rationale: matches the browser-viewer precedent in this program, keeps the contract (already JSON)
as the only coupling, and lets the renderer be developed offline against the fixture first.

**Alternatives** (pick if you prefer native/single-language):
- *Taichi (GGUI + GPU)* — consistent with the program's existing Taichi rendering pipeline; GPU
  compute is first-class. Weaker for rich dashboard widgets; good if the visuals dominate.
- *PyQt/PySide + moderngl* (or `pyqtgraph`) — strong native dashboard widgets + GPU; desktop-only,
  heavier dependency. Single Python process can drive the CLI in-process.

This is **decision #1 for your session.** The contract is stack-agnostic either way.

## 4. Progressive rendering (what it means here)

Two layers, both "coarse first, then refine":
- **Visual** — draw each view immediately at low fidelity (few samples / low-res passes), then
  accumulate to high fidelity over frames while idle (the high-quality viewing floor still applies:
  4K target, 2K minimum once settled). Natural in WebGPU via accumulate-over-frames.
- **Data** — the demo's convergence gate has a `--refine`-style knob (base vs refine× resolution).
  A "sharpen" action can re-invoke the CLI at higher refinement; channels whose `verdict` was
  borderline tighten. Show the verdict changing as it sharpens.

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

1. **Stack** — web+WebGPU+bridge (recommended) vs Taichi vs PyQt+moderngl.
2. **Bridge transport** — local HTTP server, or a one-shot subprocess per recompute, or a
   long-lived stdio worker. (HTTP is simplest; stdio is lowest-latency.)
3. **Scene caching** — cache emitted scenes by `(explore set, depth, refine)` so re-selecting a
   prior configuration is instant.
