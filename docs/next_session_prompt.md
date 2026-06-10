# Next-session prompt — build the visualizer

*(Paste the block below into a fresh session, working in `H:\character-explorer`.)*

---

You're building the **visualizer** for `character-explorer` — a repo that already contains a
finished physics *demo* and the contract it emits. Your job is the renderer/dashboard that turns
emitted scenes into an interactive, GPU-rendered learning tool. **You are not writing physics** —
that is done and lives behind a contract.

Repo: `github.com/ronviers/character-explorer`, local at `H:\character-explorer` (public, MIT). The
demo is Python 3.11+ with numpy + scipy only; emit a scene with
`python demo/character_scene.py --explore all --emit scene.json`.

**This is a learning tool, not a simulator, and it is "illustration, not evidence."** Every number
is computed on a synthetic, hand-built substrate; nothing here validates physics. That framing is
load-bearing — see the warning at the end.

## Read these first, in order
1. `README.md` — what the repo is.
2. `docs/handoff_visualizer.md` — **your brief.** Decided stack, the two camera modes, progressive
   rendering, the View→visual mapping, how the dashboard drives the CLI, the "10× growth" rules.
   Treat it as the spec.
3. `docs/architecture_scene_visualizer.md` — the `scene/v0.1` contract you render: Views, Channels
   (each carries a convergence verdict), Axes (kinds: value / structural / observer).
4. `docs/fake_nan_discipline.md` — why every value carries a verdict and how you must honor it.
5. `fixtures/scene_all.json` — a complete frozen scene (9 views, 4 axes, 6 guided steps).
   **Develop against this first; you can build the whole renderer with no Python running.**

## The stack is decided — don't re-litigate
React or Svelte UI + a **TypeScript scene model** mirroring `demo/scene_contract.py` 1:1 +
**WebGPU** renderer + a thin **FastAPI** bridge that runs `character_scene.py --explore … --emit`
and returns the JSON. Python stays entirely outside the visualization process. **Not Taichi** — the
renderer runs no physics, so it earns nothing here. WebGPU from day one (it drives the GPU as fully
as native on this hardware).

## First moves (fixture-first)
1. Render `fixtures/scene_all.json` statically — all views, axes, guided steps — no backend. Get
   the View vocabulary and verdict styling right.
2. Axis controls: **value** axes are sliders that index pre-swept channels (no recompute);
   **structural** axes (`depth`) trigger a recompute; the **observer** axis (`tau_obs`) is the
   camera (below).
3. Guided/open toggle; default guided; walk q1→q6.
4. Then the bridge, so structural changes re-invoke the CLI.
5. Then progressive rendering.

## Non-negotiables
- The renderer runs **no physics** — render computed data, never recompute it.
- **Honor `Channel.verdict`:** `converged`/`analytic` → render as fact; `boundary_tripwire` (value
  arrives as `null`) → a distinguished edge-state; `unconverged`/`fake_nan_cleared` → never as fact.
- **Two camera modes, standard is default** (handoff §3b): *standard* = conventional tumble / pan /
  dolly spatial camera; *τ_obs mode* = the camera couples to the observation-scale axis (ride the
  RG flow). Don't force the scale-camera on a learner still orienting.
- **Surface `meta.framing` persistently** — "illustration, not evidence" and "the FDR view is
  calibration, not a test" must stay visible, not dismissable to nothing.
- **Guided mode default** — a lost learner gives up.

## Open decisions left to you (handoff §9)
Bridge transport (lean long-lived stdio/websocket for the future streaming path); scene caching;
and *when* to add the `field` view kind + streaming + per-element `τ_obs` coordinates — **not the
first cut.** The discrete views + the fixture are enough to ship something real.

## The one thing to be afraid of — read before you fall in love with the rendering
The hard part of this project is **not** the renderer. It is that a beautiful, responsive,
GPU-slick interactive *manufactures a false sense of discovery*. When a learner drags a slider and
the current "responds," it feels like an experiment — but they are reading a pre-baked lookup table
over a hand-built substrate. The more gorgeous and immediate the tool, the stronger the illusion
that they are doing science rather than reading an illustration, and the more confidently they walk
away holding a compressed, subtly-false model. Every compression (the marginal-point "horizon," the
clean monotone splits, the affinity numbers that look discovered) is a place to teach something
crisp and wrong, and crisp-wrong outlives fuzzy-true.

So your job is not only to render the data faithfully — it is to **keep the seams visible**: make
the truth *"this is an illustration; you are not experimenting on nature"* survive contact with a
delightful interface. Favor designs that teach the **idea** and reveal their own scaffolding over
designs that maximize the feeling of live experimentation. When a choice trades a little polish for
a lot of honesty, take the honesty.

Start by reading the five files, then render the fixture.
