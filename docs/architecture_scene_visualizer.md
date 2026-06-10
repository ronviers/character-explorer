# Architecture — a general scene visualizer; "character" as one scene source

Status: design (2026-06-10). Two commitments shape this:

1. **Learner-first inputs.** The demo's input surface is organized around *what a learner is
   curious about*, not around parameter names. Each input is a question the learner asks and a
   consequence they watch.
2. **A general contract.** The handoff abstracts away from "character" into a domain-neutral
   **scene**. The visualizer is a general apparatus that renders any scene; the character
   storyline is one **scene source** among future others. The NaN/convergence discipline lives in
   the general contract, not in the character code.

Demonstrator today: [`demo/character_storyline_demonstrator.py`](../demo/character_storyline_demonstrator.py)
— console-only, hardcoded substrate. This turns it into a scene source that bakes a learner's
curiosity into a precomputed, scrubbable scene, plus a general visualizer that renders it.

---

## 1. The learner's questions (the spine that drives input design)

A learner does not want to set `γ_AB`. They want to *find out* something and watch it happen. The
input surface is these questions, in a learning order. Each is one exploration; each bakes a
**scrubbable axis** (§3) so the learner can move the knob and see the consequence.

| The learner asks… | The move (input) | What they watch | The idea it lands |
|---|---|---|---|
| **What makes a flow that doesn't average away?** | toggle the loop's frustration; add the 3rd node | the circulation 𝒜 jumps 0 → nonzero | a persistent current needs a *frustrated* loop; two nodes give only a gyrator, three is the minimum |
| **Is that flow a stored thing or a kept-up thing?** | turn the drive down to zero | the current follows the drive to 0 | it is *sustained, not stored* — remove the drive and it's gone |
| **I can measure it two ways — why do they agree?** | view the heat ledger beside the current ledger | both read the same dissipation σ | one dissipation, two ledgers (`J·𝒜 = ∫FDR departure`) |
| **What happens if I push it to the extreme?** | push toward an edge (drive→0, memory→memoryless, scales→merging) | the observable degenerates; the gate flags the boundary | character lives in the **open interior** — edges are approached, never reached |
| **How does complexity build up?** | stack levels (raise the cascade depth) | the tower; dissipation climbs, cost paid downward; depth caps out | structure climbs the protected subspace, paid for by erasure below |

Two design consequences:
- **Inputs are framed as experiments, not parameters.** The CLI verb is `--explore minting`, not
  `--frustration on`. The expert parameter knobs still exist underneath (§5) for fine control, but
  they are not the learner's front door.
- **The fourth question is the keystone.** Pushing toward a boundary is where the interior-only
  discipline *and* the NaN gate become the lesson: the learner sees an observable degenerate and
  the apparatus refuse to read a value *at* the edge. The "fake NaN" discipline (below) is not
  plumbing the learner is shielded from — approached carefully, it is the most instructive view.

---

## 2. The general contract — `scene/v0.1` (domain-neutral)

The visualizer consumes a **Scene**: a set of typed **Views**, whose data are **Channels**, some
indexed by scrubbable **Axes**. Nothing in this vocabulary mentions character.

```jsonc
{
  "schema": "scene/v0.1",
  "meta": {
    "title": "...",
    "framing": [ {"kind":"disclaimer","text":"illustration, not evidence"},
                 {"kind":"note","text":"every quantity built in; Step 3 is calibration"} ],
    "guided": [ {"axis":"frustration","prompt":"turn frustration off — where did the current go?"} ]
  },
  "axes": [
    { "name":"frustration", "label":"is the loop frustrated?", "values":[false,true] },
    { "name":"drive",       "label":"how hard is it driven?",  "values":[0,0.1,0.3,0.6,1.0] }
  ],
  "views": [ /* typed panels, below */ ],
  "provenance": { "source":"character", "seed":..., "refine_factor":2, "generated_at":"<injected>" }
}
```

**Channel** — the atom. Carries a value (or values over axes) *and its convergence verdict*:

```jsonc
"channel": {
  "value": 9.58,                       // scalar; OR
  "over": ["drive"], "values": [0,0.04,0.40,1.58,4.39],   // indexed by axis "drive"
  "unit": "nats/cycle",
  "verdict": "converged",              // converged | boundary_tripwire | unconverged | fake_nan_cleared
  "role": "primary"                    // primary | reference
}
```

**View kinds** — the fixed, domain-neutral vocabulary (a scene source maps its content onto these):

| kind | data | a character act that uses it | a *different* domain that uses it |
|---|---|---|---|
| `graph` | nodes, directed/signed edges, layout, per-node & per-edge channels, a flow channel | minting: the cycle with a circulation channel | a reaction network; a food web |
| `series` | x-axis, named traces y(x), event markers | relaxation: J(t), g(t), "drive off" marker | a training loss curve; populations over time |
| `locus` | parametric 2-D points, reference lines/branches with labels | FDR plot: χ vs ΔC, slope-1 and slope-X branches | a phase portrait; an ROC curve |
| `spectrum` | complex-plane points, grouped/labeled | the Jacobian eigenvalues, onset pair highlighted | any eigen/pole plot |
| `hierarchy` | ordered levels, per-level channels, inter-level flow channels, a cutoff marker | cascade: the tower, σ split, ε→1 cutoff | trophic levels; a multigrid stack |
| `sweep` | control x → observable y, regime bands, a "boundary approached" marker | the ε→1 / drive-lock sweeps | rate-constant → steady state |
| `readout` | named scalar channels with units + verdicts | σ = J·𝒜, the heat per bath | any panel of computed numbers |
| `field` *(planned, v0.2)* | a sampled grid / texture-backed channel | circulation as a vector field; an uncertainty field | any continuous field (a density, a flow) |

Each view binds its channels by name; the visualizer knows how to *draw a `graph` with a flow
channel*, not what "minting" is. Labels and prompts come from the scene source via `meta`/`label`.

**Growth note (the vocabulary is discrete today).** The kinds above are all discrete marks. As the
project scales, scalars become *fields* (circulation → a vector field, gate verdicts → an
uncertainty field) — hence the planned `field` kind and a texture-backed channel. Build the
renderer's primitive set with a field/texture pass from the start so this is additive. Two
companion contract evolutions travel with it: (1) **streaming / partial scenes** — emit static
geometry first, then coarse channels, then refined channels, so progressive refinement runs
end-to-end (compute→pixel), not just in the renderer; this is the answer to the first real wall,
which is *scene-generation cost* (a monolithic emit, doubled by the gate's base+refine×), not
rendering. (2) **forward-compatibility** — a renderer **skips unknown view kinds** and surfaces
them rather than crashing; pin the major schema version, tolerate unknown minors, keep evolution
additive.

---

## 3. Axes — how a physics-free visualizer is interactive

The visualizer runs **no physics** (the standing discipline: a renderer is a rendering, not a
sim). So interactivity is not recomputation — it is **scrubbing precomputed samples**. The scene
source bakes the learner's curiosity into axes: a channel indexed `over: ["drive"]` carries its
value at every sampled drive. The visualizer renders one slider per axis; moving it indexes the
channels. The author decides *which questions are scrubbable*; the learner explores within them.

This is the whole mechanism behind §1: each `--explore X` adds the axis (or axes) that answers
question X and pre-sweeps every affected channel. "Facilitate curiosity" = bake the right axes and
hand them to the learner as labelled, consequence-bearing knobs.

(An axis may be discrete — `frustration:[false,true]` — or sampled-continuous — `drive:[0..1]`.
Cross-products are allowed but cost precompute; the source caps total samples and `log()`s what it
dropped, never silently truncating a sweep.)

Three axis **kinds** (`Axis.kind`): **value** (pre-swept; scrub = index = a uniform update over
resident geometry), **structural** (changes geometry/topology — node count, cascade depth — so
scrub triggers a recompute / re-invoke), and **observer** (the observation-scale coordinate
`τ_obs`; pre-swept like value, but the visualizer binds it to the **camera** and uses `|Δτ_obs|`
for level-of-detail — see [`handoff_visualizer.md`](handoff_visualizer.md) §3b). Exactly one
observer axis per scene; it is the camera. `validate()` rejects a value/observer axis that nothing
is swept over (the conflation that hides a recompute behind a fake scrubber).

---

## 4. The convergence gate — general, in `Channel.verdict`

The "fake NaN" discipline (synthetic two-mode kernel flood, 2026-05-27) is a property of the
**general apparatus**, because *any* scene source can push an observable to a boundary — and this
one's axes deliberately do (drive→0, memory→memoryless, scales→merging). A NaN is never filled; it
is either a bad test or the genuine §Asymptotic-closure boundary tripwire, discriminated by
**refinement-invariance** (recompute at finer dt/grid: fake artifacts vanish or move, a genuine
boundary does not). The quiet form is worse — *no NaN ≠ trustworthy*; un-converged graded values
drift under refinement.

So every graded channel is produced through a gate that recomputes at `refine×` resolution and
stamps a verdict:

```
gate(fn, inputs, refine) -> Channel{ value, verdict }
  NaN/inf + vanishes on refine -> fix apparatus or "fake_nan_cleared"   (never fill)
  NaN/inf + refinement-stable  -> "boundary_tripwire"  (falsification candidate; emit AS SUCH)
  finite + stable under refine -> "converged"
  finite + drifts              -> "unconverged"  (HALT + name channel + inputs)
```

The verdict travels to the pixel. The visualizer's contract: render `converged` as fact; render a
`boundary_tripwire` as a distinguished edge-state (the degenerate face lit — for the learner, the
*answer* to "what's at the extreme?"); never render `unconverged`/`fake_nan_cleared` as fact. The
gate never clips a state variable at 0 (that manufactures the excluded boundary); it uses
spontaneous-floor / vanishing-noise so an edge is approached, never attained.

Baseline for the current computations (so the gate has expectations to assert): `α_s` is
refinement-invariant to 4 digits (exact `expm` propagators); `⟨σ⟩` MC carries a ~1% dt-bias that
halves under dt/2 (the analytic Lyapunov value is exact and is the primary channel).

---

## 5. The character scene source (one source; the CLI lives here)

A scene source = a module that computes a domain and emits a `scene/v0.1`. The character source
maps the five acts onto Views and the learner questions onto Axes.

```
python -m character_scene \
  --explore minting          # Q1 → axes: frustration[off,on], n_nodes[2,3]; views: graph, readout(𝒜), spectrum
  --explore drive            # Q2 → axis: drive[1→0]; views: series(J,g)
  --explore ledgers          # Q3 → views: readout(σ=J·𝒜, heat), locus(FDR)
  --explore boundary         # Q4 → axis: toward[a→0|β→1|ε→1]; views: sweep, readout(+verdicts)
  --explore cascade          # Q5 → axis: depth[1..d]; views: hierarchy
  --explore all              # the whole storyline as one multi-axis scene
  --emit scene.json

  # expert overrides (not the learner's front door):
  --graph "1->2:+ 2->3:+ 3->1:-"  --add-edge "1->3:- nonrecip g=0.4"
  --eps-ladder 0.1,0.3,0.6  --beta 0.5 --temps 1.5,1.0,0.6 --refine 2 --seed ...
```

- **`--explore` is the learner's verb**; it selects which axes are baked and which views appear.
- **Edges** (`--graph`/`--add-edge`) are the expert form of Q1's "add the 3rd node": signed
  directed edges `FROM->TO:SIGN [nonrecip] [g=W]`. The source validates Harary frustration and
  refuses a 2-cycle-only graph ("gyrator, not a minted bit — add a node"): the Trap-1 guard
  becomes Q1's lesson rather than a hidden assertion.
- **Cascade depth** is the expert form of Q5; the ε-ladder sets each level's timescale ratio, and
  the `hierarchy` view marks the usable depth where εₖ→1 caps the tower.

Source internals stay three pure layers — `builder` (args → operators), `engine` (five acts, each
a pure `spec → observables`, reusing the already-tested `ness_ep` / `affinity_from` / GLE
embedding), `gate` (wraps every graded read) — and a `scene` assembler that arranges the obs into
Views/Channels/Axes. Console mode renders the same obs for humans; `--emit` writes the scene.

---

## 6. The visualizer (the general apparatus — a separate session)

Inherits a frozen brief, no live code:
1. **Input:** any `scene/v0.1`. Knows nothing of character; pins the schema version.
2. **Render the View vocabulary** (graph/series/locus/spectrum/hierarchy/sweep/readout) by
   *composing GPU primitives* (marks + fields + annotations), not a widget per kind. Adding a new
   domain — or a new view kind — is a new scene source / composition, *not* an engine rewrite. An
   **unknown view kind is skipped and surfaced, never fatal.**
3. **Expose Axes as controls**; scrubbing indexes precomputed channels. No physics, no recompute.
   *Value*-axes update uniforms (geometry stays resident); *structural*-axes (node count, depth)
   rebuild or switch geometry — see [`handoff_visualizer.md`](handoff_visualizer.md) §3a.
4. **Honor `Channel.verdict`** (render fact / edge-state / refuse) — this is general, not per-domain.
5. **Surface `meta.framing` and `meta.guided`** — disclaimers are first-class UI; guided prompts
   nudge the learner ("turn frustration off — where did the current go?").
6. High-quality viewing floor (4K default / 2K min).

The win of the abstraction: the visualizer is built and hardened once against `scene/v0.1`; every
future domain (and every future character experiment) is a scene source feeding the same renderer.

---

## 7. Open decisions (your steer)

1. **Implement order.** Three pieces: (a) the character source's `--explore` + scene emit, (b) the
   `scene/v0.1` schema as frozen dataclasses, (c) the visualizer (separate session). I'd build
   (b) then (a) this track, leaving (c) for its own session against the frozen schema. Go?
2. **Axis granularity.** Continuous axes sampled at ~5 points by default (cheap, scrubbable);
   bump per-explore if a curve needs resolution. Good default, or finer?
3. **Guided vs open.** `meta.guided` ships author-written prompts per axis. Want the learner led
   through Q1→Q5 in order (a guided tour mode), free to roam (open), or both with a toggle?
```
