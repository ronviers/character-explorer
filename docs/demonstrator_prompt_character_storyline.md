# Demonstrator: the character storyline end-to-end on a synthetic frustrated triad
# (illustration, NOT evidence)

## What this is / is not
- IS: one runnable Python script walking the five acts of the character storyline —
  minting → energetics → FDR/memory calibration → the conjugate-cascade ledger →
  drive-sustained relaxation — on a synthetic linear driven-dissipative substrate.
- IS NOT: evidence for, or validation of, the framework. The substrate is hand-built;
  every quantity it displays is built in. It illustrates the storyline; it does not test it.
  In particular, Step 3 is estimator calibration, NOT a pass of the β-collapse falsifier
  (the framework's sharpest test — it needs real laboratory data + the inversion pipeline,
  and has not been run).

## Discipline to hold throughout
- Observables live in OPEN intervals. The degenerate faces {a=0, β=1, ε=1, D→∞} are reached
  only as limits. Never formulate a readout *at* a boundary; approach from the interior and
  report the approach.
- The load-bearing minting invariant is the gauge-invariant Schnakenberg cycle affinity 𝒜.
  The complex-conjugate Jacobian pair is reported as the underdamped *onset signature* and is
  explicitly NOT the invariant (a coupling-created complex pair can deform back through ω=0
  without rewiring; 𝒜 cannot).
- Reference: H:\character-framework\framework\character.md — §Frustration and the protected
  current, §Two fluctuation-dissipation readings, §The conjugate cascade, §Coarse-graining and
  the marginal point. Reusable apparatus: experiments\cycle_affinity.py, gyrator_minting.py,
  reset_redrive_test.py; mpa-solver (Caputo closure, fit_invariants, linearize).

## Substrate (one family, used across all five steps)
- N ≥ 3 modes — minimum, so the coupling graph can carry a genuine frustrated 3-cycle.
  A 2-cycle current is gauge-REMOVABLE, so two 1-D OU nodes mint only a gyrator
  (current-only N=2), NOT a topological bit. N=3 is the minimal carrier; build for it.
- Two UNFRUSTRATED parts: Part A detailed-balanced in isolation (reciprocal coupling, 𝒜_A=0),
  Part B detailed-balanced in isolation (𝒜_B=0). The coupling ⊗ adds non-reciprocal edges that
  close a directed, sign-frustrated 3-cycle in the union graph.
- Realizations: Step 1 (spectral/affinity minting) — overdamped OU, for a clean
  complex-pair-on-coupling signature. Steps 2–5 (energetics, ledger, relaxation) — the SAME
  3-cycle topology realized as underdamped Langevin oscillators (position + momentum) so heat
  is well-defined. State the correspondence explicitly: same directed cycle, same
  sign-frustration, same nonzero 𝒜.

## Step 1 — Minting (topological)
- Show each part in isolation is detailed-balanced: 𝒜 = ln(∏ forward k / ∏ backward k) around
  its cycle evaluates to 0 (equivalently drift·diffusion is symmetric). Print 𝒜_A, 𝒜_B.
- Couple via ⊗; show the union graph contains a frustrated 3-cycle (odd number of negative
  edges, irremovable by node sign-relabeling — DEMONSTRATE gauge-invariance: relabel nodes,
  show 𝒜 unchanged).
- Print the Jacobian spectrum before and after coupling; show the emergent complex-conjugate
  pair, labeled as the underdamped onset signature (NOT the invariant).
- Compute and print the nonzero union affinity 𝒜_AB; verify it is gauge-irremovable and
  drive-locked (forced nonzero at any nonzero drive). This 𝒜 is the load-bearing minting
  diagnostic.

## Step 2 — Energetics (momentum, heat)
- Underdamped Langevin realization of the same 3-cycle, modes coupled to baths at distinct
  temperatures (T1 ≠ T2). Euler–Maruyama or Milstein; explicitly track position and momentum.
- Compute stochastic heat to each bath along trajectories (Sekimoto stochastic energetics).
- Verify the time-averaged total entropy production equals the intrinsic ⟨σ⟩ = J·𝒜, reported
  WITH its Monte-Carlo error bar. This is a stochastic average — agreement is to sampling
  accuracy, not machine precision. State the error explicitly.

## Step 3 — FDR / memory CALIBRATION (not a test)
- Header this step in the output: estimator calibration of the inversion machinery; NOT a
  measurement, NOT a β-collapse pass. A finite linear Markov system has no aging — the memory
  here is IMPORTED, by hand.
- Impose a known memory exponent β (strictly 0 < β < 1, interior) by integrating a generalized
  Langevin equation with a fractional / Mittag-Leffler kernel (or its sum-of-exponentials
  approximation, cf. the mpa-solver Caputo closure).
- From the trajectories compute the two-time correlation C(t, t_w) and the perturbative
  response R(t, t_w); form the FDR-violation ratio X < 1 and extract the aging slope α_s.
- Confirm the pipeline recovers α_s ≈ β_imposed. Print both side by side and state plainly:
  equality is expected BY CONSTRUCTION (β was put in); the step verifies the estimator is
  unbiased — nothing more.
- Stay in the interior: a > 0, 0 < β < 1 strictly. If approaching the near-threshold regime,
  report it as approach, never as a readout at a ≈ 0.

## Step 4 — Conjugate-cascade ledger
- Introduce timescale separation: the minted circulation runs fast relative to a slow manifold.
  Define the contraction modulus ε as the timescale ratio (leading IR eigenvalue of the level
  map).
- Coarse-grain (integrate out the fast circulation). Compute σ_resolved (visible at the coarse
  level) and σ_hidden (dissipation of the integrated-out fast currents).
- Verify σ_total = σ_resolved + σ_hidden with σ_hidden ≥ 0. Note honestly that σ_hidden ≥ 0 is
  a theorem (Esposito) being illustrated on a worked example — it cannot come out negative.

## Step 5 — Marginal point + relaxation
- Sweep ε → 1 and show the timescale separation fails / the slow manifold ceases to persist
  (loss of normal hyperbolicity). Report as APPROACH to the marginal point, not evaluation at
  ε = 1.
- Remove the drive; show the explicit time-series relaxation of the protected circulation
  J(t) → 0 as the system returns to the disordered fixed point — demonstrating the branch is
  sustained by the drive, not stored.

## Output requirements
- Fully executable Python, numpy/scipy only (target machine: numpy 2.4, scipy 1.17). One
  script, runnable top to bottom.
- Console output: 𝒜_A, 𝒜_B, 𝒜_AB; Jacobian eigenvalues before and after coupling; ⟨σ⟩ from
  energetics with error bar and the J·𝒜 comparison; imposed β vs recovered α_s; the cascade
  ledger σ_total / σ_resolved / σ_hidden; a summary of the relaxation J(t) trace.
- A brief physical interpretation of the SDE results.
- MANDATORY honest-framing header (in the script docstring AND printed at runtime): this is a
  synthetic pedagogical demonstrator; every quantity is built in; it illustrates the storyline
  and does not validate the framework; Step 3 is estimator calibration, not a β-collapse pass.

---

