# character-explorer

An interactive, learner-first explorer for the **character** storyline — the structure that
finite drive imprints on driven-dissipative steady states (minting a protected current →
energetics → memory/FDR → a conjugate-cascade ledger → drive-sustained relaxation).

> ### ⚠️ Illustration, not evidence
> Everything here runs on a **synthetic, hand-built substrate**. Every quantity it displays is
> **built in** — it *illustrates* the storyline, it does **not** test or validate any physical
> claim. The FDR view in particular is **estimator calibration** (a memory exponent imposed by
> hand and recovered), **not** a pass of any falsifier. Observables live in the **open interior**;
> the degenerate edges are *approached*, never evaluated. This is a teaching apparatus.

The framework it illustrates lives in a separate repo,
[character-framework](https://github.com/ronviers/character-framework). This repo is the *demo*
and (soon) its *visualizer*; keeping them apart is deliberate, so nothing here is mistaken for a
result.

---

## What's in here

| Piece | Path | What it is |
|---|---|---|
| **Storyline demonstrator** | [`demo/character_storyline_demonstrator.py`](demo/character_storyline_demonstrator.py) | One runnable script, console-only, that walks the five acts on a synthetic frustrated triad. |
| **Scene contract** | [`demo/scene_contract.py`](demo/scene_contract.py) | A **domain-neutral** handoff schema, `scene/v0.1`. No mention of "character" — a general visualizer renders any *scene*. |
| **Character scene source** | [`demo/character_scene.py`](demo/character_scene.py) | Emits a `scene/v0.1` from learner-facing `--explore` questions. "character" is one *source*. |
| **Sample scene** | [`fixtures/scene_all.json`](fixtures/scene_all.json) | A frozen `scene/v0.1` to develop the visualizer against without running the demo. |
| **Docs** | [`docs/`](docs/) | Architecture, the fake-NaN discipline, and the visualizer build handoff. |

## Quickstart

Requires Python 3.11+ with `numpy` and `scipy` (only those).

```bash
# the whole storyline, console-only (~8s)
python demo/character_storyline_demonstrator.py

# emit a scene for the visualizer (~12s)
python demo/character_scene.py --explore all --emit scene.json

# one question at a time
python demo/character_scene.py --explore minting --explore drive --emit scene.json
```

## The learner's questions (the input surface)

The inputs are organized around *what a learner is curious about*, not parameter names. Each
`--explore` is a question that bakes a scrubbable **axis** the visualizer exposes as a knob.

| `--explore` | The learner asks… | The idea it lands |
|---|---|---|
| `minting` | What makes a flow that doesn't average away? | needs a *frustrated* loop; 2 nodes is a gyrator, 3 is the minimum |
| `drive` | Is it stored, or kept up? | *sustained, not stored* — remove the drive and it's gone |
| `ledgers` | Why do two measurements agree? | one dissipation, two ledgers (`J·𝒜 = ∫FDR departure`) |
| `boundary` | What's at the extreme? | character lives in the **open interior**; edges are approached, never reached |
| `cascade` | How does complexity stack? | structure climbs the protected subspace, paid for by erasure below |

## The scene contract (`scene/v0.1`)

The demo computes everything and emits a single JSON **scene**; a visualizer renders it and runs
**no physics**. A scene is typed **views** (`graph`, `series`, `locus`, `spectrum`, `hierarchy`,
`sweep`, `readout`), **channels** that each carry a **convergence verdict**, and scrubbable
**axes** (pre-swept, so a physics-free visualizer is interactive by *scrubbing*, not recomputing).
"character" is one scene source; another domain is another source against the same contract. See
[`docs/architecture_scene_visualizer.md`](docs/architecture_scene_visualizer.md).

## The convergence gate (the "fake NaN" discipline)

Every graded number is computed through a gate that recomputes it at finer resolution and stamps a
**verdict** — `converged`, `boundary_tripwire` (a degenerate edge attained), `unconverged`, or
`fake_nan_cleared`. A NaN is **never** filled or clipped; it is diagnosed. This is why pushing the
`boundary` exploration toward an edge shows the apparatus *refuse* to read a value there — the
open-interval lesson, made visible. Full rationale:
[`docs/fake_nan_discipline.md`](docs/fake_nan_discipline.md).

## Visualizer (planned, separate session)

A GPU, progressively-rendering **dashboard** that drives the demo CLI and renders the resulting
`scene/v0.1`. The build brief is [`docs/handoff_visualizer.md`](docs/handoff_visualizer.md); start
it against [`fixtures/scene_all.json`](fixtures/scene_all.json).

## License

MIT — see [`LICENSE`](LICENSE).
