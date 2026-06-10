# The fake-NaN discipline (and the convergence gate that enforces it)

This is the load-bearing numerical-honesty rule of the demo, captured here so it does not get
lost. It is implemented as `gate()` in [`../demo/character_scene.py`](../demo/character_scene.py)
and its verdict is carried all the way into the scene contract (`Channel.verdict`).

## The rule

A `NaN`/`inf` is **never** tolerated, filled, or clipped — no `nan_to_num`, no `np.clip(x, 0, …)`
on a state variable, no silent skip. A non-finite value means exactly one of two things, and you
must diagnose which:

1. **The test is bad** (most common) — the apparatus computed something outside the claim space
   (an unstable embedding, a degenerate fit, 0/0, log 0). **Fix the apparatus.**
2. **A genuine boundary was attained** — an observable hit a degenerate value (0, 1, or ∞) at a
   finite operating point. In this framework's terms that is the *open-interval* boundary, which
   the structure forbids reaching at any finite drive. It is a real signal, not noise.

Either way a non-finite value must **halt and be diagnosed**, never propagated as if it were a
number. Clipping a state variable at 0 is itself a bad-test pattern — it *manufactures* the
excluded boundary. Approach an edge with spontaneous-floor / vanishing-noise dynamics so it is
approached but never attained.

## The two forms (why "I cleared the NaN" is not enough)

Documented from a real flood (synthetic two-mode kernel, 2026-05-27):

- **Loud form — fake NaNs.** Crossing an orthogonal/threshold zero on a *finite-step* integrator
  manufactures overflow/runaway NaNs that are **numerical artifacts**, not the genuine boundary.
- **Quiet form — un-converged values (worse, because silent).** Clearing a fake NaN by refining
  the step does **not** make the value trustworthy. Near a zero, a *finite* number is not yet a
  *converged* number — graded observables drift materially as you refine. **No NaN ≠ trustworthy.**

The single discriminator for **both** forms is **refinement-invariance**: recompute at finer
resolution (halve `dt`, double the grid). A *genuine* boundary tripwire is refinement-invariant; a
*fake* artifact vanishes or moves; an *un-converged* value drifts.

## The gate

`gate(fn, refine=2, tol)` runs `fn` at base and `refine×` resolution and classifies:

| outcome | verdict | meaning | visualizer renders as |
|---|---|---|---|
| finite, stable under refine | `converged` | trustworthy | fact |
| exact (no discretization) | `analytic` | trustworthy by construction | fact |
| non-finite, stable under refine | `boundary_tripwire` | a degenerate edge attained | a distinguished edge-state |
| non-finite, vanishes on refine | `fake_nan_cleared` | numerical artifact | **not** fact |
| finite, drifts under refine | `unconverged` | not yet trustworthy | **not** fact |

The verdict travels in the scene so the visualizer never renders an un-vetted number, and the edge
is shown *as* an edge rather than silently filled. In the `boundary` exploration the demo
deliberately evaluates an observable *at* `ε = 1`; the gate returns `boundary_tripwire` (value
`null` on the wire) — that refusal **is** the open-interval lesson.

## Where this bit, in this demo

- **Step 3 (FDR) once NaN'd** because the first GLE embedding was structurally **unstable** (a
  positive eigenvalue — even the *exact* matrix-exponential propagator diverges). That is form-1
  "bad test." The fix was to rebuild the embedding to be provably stable
  (`max Re λ(M) < 0`), with no fill/clip — see `_gle_embedding` in
  [`../demo/character_storyline_demonstrator.py`](../demo/character_storyline_demonstrator.py).
- Refinement confirmed the *cleared* result is also trustworthy (the quiet-form check):
  - `α_s` (recovered aging slope) is refinement-invariant to 4 digits — the propagators are exact
    (`expm`), so this channel is `analytic`.
  - `⟨σ⟩` from Monte-Carlo Sekimoto heat carries a ~1 % `dt`-bias that halves under `dt/2`; the
    analytic Lyapunov value is exact and is the primary channel. The MC channel is `gate`-checked
    and emits `converged`.

The lesson for anyone extending the demo: when you add a knob that pushes toward an edge (drive→0,
memory→memoryless, scales→merging), run the value through `gate()`. Clearing a NaN is the *start*
of diagnosis, not the end.
