r"""character_scene.py -- the CHARACTER scene source: emits a domain-neutral `scene/v0.1`
(see scene_contract.py) that a general visualizer renders.  "character" is ONE source.

Learner-first: the input surface is the learner's questions (--explore), each baking a
scrubbable axis the visualizer exposes as a knob.  Guided mode is the DEFAULT (a lost learner
gives up); a toggle switches to open roaming.

The five acts reuse the VALIDATED machinery from character_storyline_demonstrator.py
(ness_ep, cycle_frequency, the GLE embedding, the Caputo SoE kernel) -- this source only
parameterizes them and arranges the results into Views/Channels/Axes.

Run:
  python character_scene.py --explore all --emit scene.json
  python character_scene.py --explore minting --explore drive --emit scene.json
ILLUSTRATION, NOT EVIDENCE.  Every quantity is built in.  Step 3 (fdr) is estimator
calibration, not a beta-collapse pass.
"""
from __future__ import annotations

import sys
import argparse
import numpy as np
from numpy.linalg import eigvals
from scipy.linalg import solve_continuous_lyapunov, expm

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

from character_storyline_demonstrator import (          # validated machinery
    C3, P_PERP, ness_ep, cycle_frequency, _gle_embedding, _soe_kernel)
from scene_contract import (
    Scene, Meta, Axis, View, Channel, GuidedStep, validate,
    CONVERGED, UNCONVERGED, BOUNDARY_TRIPWIRE, FAKE_NAN_CLEARED, ANALYTIC)

RNG = np.random.default_rng(20260610)


# =====================================================================================
#  the convergence gate (general discipline; carried in Channel.verdict)
# =====================================================================================
def gate(fn, *, refine=2, tol=1e-2, unit=None, role="primary", label=None, over=None):
    r"""Run `fn(res)` at base and refine× resolution; classify and stamp a verdict.
    fn(res): recompute the observable at integer resolution multiplier res (res=1 base).
    Exact (no-discretization) observables pass res through unused -> ANALYTIC via gate_exact."""
    v0 = float(fn(1))
    v1 = float(fn(refine))
    f0, f1 = np.isfinite(v0), np.isfinite(v1)
    if not (f0 and f1):
        if f1 and not f0:                                   # vanished on refine -> artifact
            return Channel(value=v1, unit=unit, verdict=FAKE_NAN_CLEARED, role=role, label=label)
        return Channel(value=v0 if f0 else float("nan"), unit=unit,    # persists -> the edge attained
                       verdict=BOUNDARY_TRIPWIRE, role=role, label=label)
    drift = abs(v1 - v0) / max(abs(v1), 1e-12)
    verdict = CONVERGED if drift <= tol else UNCONVERGED
    return Channel(value=v1, unit=unit, verdict=verdict, role=role, label=label)


def exact(value, *, unit=None, role="primary", label=None, over=None, values=None):
    """An analytic (exact, no discretization) channel -- trustworthy by construction."""
    return Channel(value=value, values=values, over=over, unit=unit,
                   verdict=ANALYTIC, role=role, label=label)


# =====================================================================================
#  substrate builders (general N-node cycle; "adding edges" = entries of the drift)
# =====================================================================================
def cyclic_gen(n):
    """Antisymmetric n-cycle generator (+1 on i->i+1, -1 reverse).  n=2: gyrator; n>=3: minted."""
    M = np.zeros((n, n))
    for i in range(n):
        j = (i + 1) % n
        M[j, i] += 1.0
        M[i, j] -= 1.0
    return M


def cycle_drift(n, kappa, g):
    """Overdamped n-cycle drift B = -kappa I + g * cyclic_gen(n).  g is the non-reciprocal drive."""
    return -kappa * np.eye(n) + g * cyclic_gen(n)


def affinity(B, D):
    """Schnakenberg cycle affinity 𝒜 = ⟨σ⟩/J_cyc (the cycle_affinity.py convention)."""
    sigma, _, _ = ness_ep(B, D * np.eye(B.shape[0]))
    om0 = cycle_frequency(B)
    Jcyc = om0 / (2.0 * np.pi)
    return (sigma / Jcyc) if Jcyc > 1e-12 else 0.0, sigma, om0


def is_minted(n, g):
    """A protected topological bit requires N>=3 AND a nonzero non-reciprocal drive.
    N=2 with g!=0 is a gyrator (current-only; a 2-state cycle obeys detailed balance)."""
    return bool(n >= 3 and abs(g) > 0.0)


# =====================================================================================
#  ACTS (pure: parameters -> observables dict).  Reuse the validated machinery.
# =====================================================================================
def act_minting(drive_vals, kappa=1.0, D=0.05):
    """Q1: where does the persistent current come from?  𝒜 over the drive axis (n=3), and the
    n=2-gyrator vs n=3-minted-bit contrast at the headline drive."""
    A_over_drive, sig_over_drive = [], []
    for g in drive_vals:
        A, sig, _ = affinity(cycle_drift(3, kappa, g), D)
        A_over_drive.append(round(A, 4)); sig_over_drive.append(round(sig, 5))
    g_hi = drive_vals[-1]
    B3 = cycle_drift(3, kappa, g_hi); B2 = cycle_drift(2, kappa, g_hi)
    _, sig3, om3 = affinity(B3, D); sig2, _, _ = ness_ep(B2, D * np.eye(2))
    ev_before = eigvals(cycle_drift(3, kappa, 0.0))
    ev_after = eigvals(B3)
    return dict(
        drive_vals=list(drive_vals), A_over_drive=A_over_drive, sig_over_drive=sig_over_drive,
        n2_sigma=round(float(sig2), 5), n3_sigma=round(float(sig3), 5),
        n2_minted=is_minted(2, g_hi), n3_minted=is_minted(3, g_hi),
        spectrum_before=[[round(z.real, 3), round(z.imag, 3)] for z in ev_before],
        spectrum_after=[[round(z.real, 3), round(z.imag, 3)] for z in ev_after],
        layout=[[float(np.cos(2 * np.pi * i / 3)), float(np.sin(2 * np.pi * i / 3))] for i in range(3)],
    )


def act_energetics(g=0.6):
    """Q3 (heat side): underdamped 3-cycle, baths T1!=T2!=T3.  ⟨σ⟩ from Sekimoto heat (analytic
    + MC, gated over dt) and the intrinsic J·𝒜 decomposition."""
    K = np.array([[2.0, .3, .3], [.3, 2.0, .3], [.3, .3, 2.0]])
    gam = np.array([1.0, 1.0, 1.0]); T = np.array([1.5, 1.0, 0.6])
    I3, Z3 = np.eye(3), np.zeros((3, 3))
    M = np.block([[Z3, I3], [-K + g * C3, -np.diag(gam)]])
    Dm = np.zeros((6, 6)); Dm[3:, 3:] = np.diag(gam * T)
    Sig = solve_continuous_lyapunov(M, -2.0 * Dm)
    p2 = np.diag(Sig)[3:]
    sigma_heat = float(np.sum(gam * (p2 - T) / T))
    Jcyc = cycle_frequency(M) / (2 * np.pi)

    def mc_sigma(res, base_dt=2e-3, N=3000, tmax=50.0):
        dt = base_dt / res; ns = int(tmax / dt); burn = ns // 5
        rng = np.random.default_rng(11)
        q = rng.standard_normal((N, 3)) * .3; p = rng.standard_normal((N, 3)) * .3
        sq = np.sqrt(dt); namp = np.sqrt(2 * gam * T); hQ = np.zeros((N, 3)); tacc = 0.0
        for k in range(ns):
            dW = rng.standard_normal((N, 3)) * sq; bath = -gam * p * dt + namp * dW
            f = (-q @ K.T) + g * (q @ C3.T); pn = p + f * dt + bath; qn = q + p * dt
            if k >= burn:
                hQ += bath * 0.5 * (p + pn); tacc += dt
            q, p = qn, pn
        return float(np.sum(np.mean(-hQ / tacc, axis=0) / T))

    sigma_mc = gate(mc_sigma, tol=2e-2, unit="nats/time", label="⟨σ⟩ (MC, Sekimoto heat)")
    return dict(sigma_heat=round(sigma_heat, 4), heat_per_bath=[round(x, 4) for x in gam * (T - p2)],
                Jcyc=round(float(Jcyc), 4), affinity=round(sigma_heat / Jcyc, 3), sigma_mc=sigma_mc)


def act_fdr(beta=0.5, tau_c=0.1, T=1.0):
    """Step 3: estimator CALIBRATION (NOT a test).  Impose beta via a Caputo SoE kernel; recover
    the aging slope α_s; equilibrium FDT self-check X_eq≈1; hot-quench aging X_aging<1."""
    c, nu = _soe_kernel(beta, tau_c, K=14)
    # (a) alpha_s from free-particle subdiffusion (gated over the integration grid)
    Mvs, Dvs = _gle_embedding(c, nu, kq=0.0, T=T); Mvs, Dvs = Mvs[1:, 1:], Dvs[1:, 1:]
    Svs = solve_continuous_lyapunov(Mvs, -2.0 * Dvs)

    def alpha(res, nS=8000):
        s = np.linspace(0.0, 800.0, nS * res); ds = s[1] - s[0]
        Cvv = np.array([(expm(Mvs * si) @ Svs)[0, 0] for si in s[::1]])
        tg = np.logspace(0.7, 2.6, 30)
        msd = np.array([2.0 * np.trapezoid(np.clip(t - s[s <= t], 0, None) * Cvv[s <= t], dx=ds) for t in tg])
        w = (tg > 20) & (tg < 400) & (msd > 0)
        return float(np.polyfit(np.log(tg[w]), np.log(msd[w]), 1)[0])

    alpha_s = gate(alpha, tol=2e-2, label="α_s (recovered aging slope)")
    # (b) FDR ratio X: equilibrium self-check + hot-quench aging branch (analytic propagators)
    M, Dmat = _gle_embedding(c, nu, kq=0.3, T=T)
    Seq = solve_continuous_lyapunov(M, -2.0 * Dmat)
    taus = np.linspace(0.0, 25.0, 500)
    Ceq = np.array([(expm(M * t) @ Seq)[0, 0] for t in taus]); R = np.array([expm(M * t)[0, 1] for t in taus])
    chi = np.concatenate([[0.0], np.cumsum(0.5 * (R[1:] + R[:-1]) * np.diff(taus))])
    X_eq = float(np.polyfit(Ceq[0] - Ceq, chi, 1)[0] * T)
    kh, tw = 3.0, 8.0
    s = np.linspace(0.0, tw, 400); dss = s[1] - s[0]
    Stw = sum(expm(M * si) @ (2 * Dmat) @ expm(M * si).T * dss for si in s) + expm(M * tw) @ (kh * Seq) @ expm(M * tw).T
    t2 = np.linspace(0.0, 80.0, 500)
    C2 = np.array([(expm(M * t) @ Stw)[0, 0] for t in t2]); R2 = np.array([expm(M * t)[0, 1] for t in t2])
    chi2 = np.concatenate([[0.0], np.cumsum(0.5 * (R2[1:] + R2[:-1]) * np.diff(t2))])
    X_aging = float(np.polyfit((C2[0] - C2)[300:495], chi2[300:495], 1)[0] * T)
    locus = [[round(float(C2[0] - C2[i]), 4), round(float(chi2[i]), 4)] for i in range(0, 500, 12)]
    return dict(beta=beta, alpha_s=alpha_s, X_eq=round(X_eq, 3), X_aging=round(X_aging, 3),
                T_eff=round(T / X_aging, 2), fdr_locus=locus,
                C_tau=[[round(float(taus[i]), 3), round(float(Ceq[i]), 4)] for i in range(0, 500, 20)])


def act_cascade(depth, eps0=0.45, kappa0=5.0, g=0.8, D=0.05):
    """Q5: conjugate-cascade ledger over `depth` levels.  Each level a minted 3-cycle at a
    geometric rate ladder; σ_hidden,k = that level's own circulation EP (the demonstrator's
    validated cross-check); ledger σ_total = Σ σ_hidden + σ_resolved(top)."""
    rates = [kappa0 * (eps0 ** k) for k in range(depth)]        # fast -> slow
    eps = [round(rates[k + 1] / rates[k], 3) for k in range(depth - 1)]
    sig_levels = [ness_ep(cycle_drift(3, r, g), D * np.eye(3))[0] for r in rates]
    sigma_resolved = round(float(sig_levels[-1]), 4)            # slowest (coarse) level
    sigma_hidden = [round(float(s), 4) for s in sig_levels[:-1]]
    sigma_total = round(float(sum(sig_levels)), 4)
    marginal = 0.9
    usable_depth = 1 + sum(1 for e in eps if e < marginal)
    levels = [dict(k=k, rate=round(rates[k], 3),
                   eps=(eps[k] if k < len(eps) else None),
                   sigma=round(float(sig_levels[k]), 4),
                   role=("resolved" if k == depth - 1 else "hidden")) for k in range(depth)]
    return dict(depth=depth, levels=levels, eps=eps, sigma_total=sigma_total,
                sigma_resolved=sigma_resolved, sigma_hidden=sigma_hidden,
                ledger_holds=all(s >= -1e-9 for s in sigma_hidden), usable_depth=usable_depth)


def act_relaxation(kf=5.0, gf=0.8, D=0.05):
    """Q2: stored or sustained?  J(t) over time as the drive is ramped off (the `time` axis)."""
    Nens, dt = 4000, 5e-3
    t_off, tau_ramp, t_end = 3.0, 0.8, 8.0
    n_end = int(t_end / dt)
    C3p = P_PERP @ C3 @ P_PERP.T
    B_drv = -kf * np.eye(3) + gf * C3
    Sig_drv = solve_continuous_lyapunov(B_drv, -2.0 * D * np.eye(3))
    x = RNG.multivariate_normal(np.zeros(3), Sig_drv, size=Nens)
    sq = np.sqrt(dt); ts, Js, gs = [], [], []
    for k in range(n_end):
        t = k * dt
        g = gf if t < t_off else gf * np.exp(-(t - t_off) / tau_ramp)
        B = -kf * np.eye(3) + g * C3
        x = x + (x @ B.T) * dt + np.sqrt(2.0 * D) * (RNG.standard_normal((Nens, 3)) * sq)
        if k % 16 == 0:
            uv = x @ P_PERP.T; Cov = np.cov(uv.T); Bp = -kf * np.eye(2) + g * C3p
            ts.append(round(t, 3)); Js.append(round(0.5 * float((Bp @ Cov - Cov @ Bp.T)[0, 1]), 5))
            gs.append(round(float(g), 4))
    return dict(t=ts, J=Js, g=gs, t_off=t_off,
                J_driven=round(float(np.mean([j for t, j in zip(ts, Js) if t < t_off])), 4),
                J_final=round(float(np.mean([j for t, j in zip(ts, Js) if t > t_end - 1.0])), 5))


def act_boundary(kf=5.0):
    """Q4: what's at the extreme?  Sweep ε -> 1 (interior, observable diverges) and show the
    apparatus REFUSE a readout AT the edge (the open-interval lesson)."""
    eps_vals = [0.5, 0.8, 0.9, 0.95, 0.99]
    gap = [round(kf * (1 - e), 3) for e in eps_vals]                 # spectral gap, closes -> 0
    heavy_traffic = [round(1.0 / (1.0 - e), 2) for e in eps_vals]    # 1/(1-ε), Kingman; diverges

    def cost_at(eps):                                               # 1/(1-ε); inf (not a crash) at ε=1
        with np.errstate(divide="ignore"):
            return float(np.divide(1.0, 1.0 - eps))
    at_edge = gate(lambda res: cost_at(1.0), label="observable AT ε = 1 (the edge)")  # -> BOUNDARY_TRIPWIRE
    return dict(eps_vals=eps_vals, gap=gap, heavy_traffic=heavy_traffic, at_edge=at_edge)


# =====================================================================================
#  EXPLORATIONS: each learner question -> (axes, views, guided step).  Guided is default.
# =====================================================================================
def explore_minting(P):
    o = act_minting(P["drive_vals"])
    ax = Axis(name="drive", label="how hard is it driven?", values=o["drive_vals"])
    edges = [dict(**{"from": i, "to": (i + 1) % 3, "sign": 1, "reciprocal": False}) for i in range(3)]
    views = [
        View(kind="graph", id="minting.graph", title="the coupling loop",
             explain="three modes in a frustrated cycle; the circulating current is the minted bit",
             data=dict(nodes=[0, 1, 2], edges=edges, layout=o["layout"],
                       circulation=exact(None, over=["drive"], values=o["A_over_drive"],
                                         unit="nats/cycle", label="circulation 𝒜"))),
        View(kind="spectrum", id="minting.spectrum", title="Jacobian eigenvalues",
             explain="a complex pair appears when the loop is driven -- the onset signature, not the invariant",
             data=dict(before=o["spectrum_before"], after=o["spectrum_after"])),
        View(kind="readout", id="minting.contrast", title="gyrator vs minted bit",
             explain="N=2 carries a current but no topological bit; N=3 is the minimal minted bit",
             data=dict(affinity=exact(o["A_over_drive"][-1], over=["drive"], values=o["A_over_drive"],
                                      unit="nats/cycle", label="𝒜 (3-cycle)"),
                       n2_sigma=exact(o["n2_sigma"], unit="nats/time", label="⟨σ⟩ N=2 (gyrator)"),
                       n3_sigma=exact(o["n3_sigma"], unit="nats/time", label="⟨σ⟩ N=3 (minted)"),
                       n2_minted_bit=exact(o["n2_minted"], label="N=2 mints a bit?"),
                       n3_minted_bit=exact(o["n3_minted"], label="N=3 mints a bit?"))),
    ]
    step = GuidedStep(id="q1", title="Where does the flow come from?",
                      prompt="Turn the drive down to 0 — watch the circulation vanish. Then ask: why isn't two nodes enough?",
                      view="minting.graph", axis="drive")
    return [ax], views, step


def explore_drive(P):
    # No scene-level axis here: time is the series view's OWN x-dimension (already carried by
    # x/traces), not a parameter you sweep. The renderer offers a playhead over the series.
    o = act_relaxation()
    views = [View(kind="series", id="drive.relax", title="is it stored, or kept up?",
                  explain="J(t) is the current; g(t) is the drive. Remove the drive and the current follows it to zero.",
                  data=dict(x=o["t"], x_label="time",
                            traces=[dict(name="|J| (current)", y=[abs(v) for v in o["J"]]),
                                    dict(name="g (drive)", y=o["g"])],
                            markers=[dict(x=o["t_off"], label="drive ramp starts")],
                            J_driven=exact(o["J_driven"], label="J while driven"),
                            J_final=exact(o["J_final"], label="J after drive off")))]
    step = GuidedStep(id="q2", title="Stored or sustained?",
                      prompt="Play the series past the ramp. The current decays to ~0 — it was never stored, only sustained by the drive.",
                      view="drive.relax")
    return [], views, step


def explore_ledgers(P):
    e = act_energetics(); f = act_fdr()
    views = [
        View(kind="readout", id="ledgers.sigma", title="one dissipation, two ledgers",
             explain="the heat ledger and the current ledger read the SAME σ (J·𝒜 = ∫FDR departure)",
             data=dict(sigma_heat=exact(e["sigma_heat"], unit="nats/time", label="⟨σ⟩ (heat ledger)"),
                       sigma_current=exact(round(e["Jcyc"] * e["affinity"], 4), unit="nats/time",
                                           label="J·𝒜 (current ledger)"),
                       sigma_mc=e["sigma_mc"],
                       heat_per_bath=exact(e["heat_per_bath"], label="heat per bath"))),
        View(kind="locus", id="ledgers.fdr", title="fluctuation vs response (FDR) — calibration",
             explain="slope 1 is equilibrium (X=1); a shallower aging branch is the FDR violation X<1. "
                     "α_s recovers the imposed memory exponent β — this is estimator calibration, not a test",
             data=dict(points=f["fdr_locus"], x_label="C(0)−C(t,tw)", y_label="χ(t,tw)",
                       X_eq=exact(f["X_eq"], label="X (equilibrium self-check ≈1)", role="reference"),
                       X_aging=exact(f["X_aging"], label="X (aging branch <1)"),
                       T_eff=exact(f["T_eff"], label="T_eff = T/X"),
                       beta_imposed=exact(f["beta"], label="β imposed (by hand)", role="reference"),
                       alpha_s=f["alpha_s"])),     # gated channel: recovered aging slope ≈ β
    ]
    step = GuidedStep(id="q3", title="Why do two measurements agree?",
                      prompt="The heat you'd measure and the current-times-affinity are the same number — one dissipation, two ledgers.",
                      view="ledgers.sigma")
    return [], views, step


def explore_boundary(P):
    o = act_boundary()
    ax = Axis(name="toward_edge", label="push toward the edge (ε → 1)", values=o["eps_vals"])
    views = [View(kind="sweep", id="boundary.eps", title="what's at the extreme?",
                  explain="approaching ε=1 the timescale gap closes and the cost diverges — but you can never read a value AT the edge",
                  data=dict(x=o["eps_vals"], x_label="ε (compression toward the marginal point)",
                            gap=exact(None, over=["toward_edge"], values=o["gap"], label="spectral gap (→0)"),
                            cost=exact(None, over=["toward_edge"], values=o["heavy_traffic"],
                                       label="1/(1−ε) cost (→∞)"),
                            at_edge=o["at_edge"],            # verdict = boundary_tripwire
                            boundary=dict(at=1.0, label="ε = 1 (never evaluated; the open-interval wall)")))]
    step = GuidedStep(id="q4", title="What happens at the extreme?",
                      prompt="Scrub ε toward 1. The cost blows up and the gap closes — and the apparatus refuses to read a value AT ε=1. Character lives in the open interior.",
                      view="boundary.eps", axis="toward_edge")
    return [ax], views, step


def explore_cascade(P):
    depth = P["cascade_depth"]
    o = act_cascade(depth)
    # depth changes the geometry (number of levels), not values over fixed geometry -> STRUCTURAL:
    # scrubbing it re-invokes the source (--cascade-depth), it is not a pre-swept index.
    ax = Axis(name="depth", label="stack the hierarchy (cascade depth)",
              values=list(range(1, depth + 1)), kind="structural")
    views = [View(kind="hierarchy", id="cascade.tower", title="how does complexity stack?",
                  explain="each level's minted circulation is paid for as hidden dissipation below; the ledger climbs",
                  data=dict(levels=o["levels"], eps=o["eps"],
                            sigma_total=exact(o["sigma_total"], unit="nats/time", label="σ_total"),
                            sigma_resolved=exact(o["sigma_resolved"], unit="nats/time", label="σ_resolved (coarse)"),
                            sigma_hidden=exact(o["sigma_hidden"], label="σ_hidden per level (≥0)"),
                            usable_depth=exact(o["usable_depth"], label="usable depth (before ε→1 caps it)"),
                            ledger_holds=exact(o["ledger_holds"], label="σ_total = Σσ_hidden + σ_resolved, σ_hidden≥0")))]
    step = GuidedStep(id="q5", title="How does complexity build up?",
                      prompt="Add levels. Structure climbs the protected subspace; its cost is paid downward as hidden dissipation. Past ε→1 the tower stops converging.",
                      view="cascade.tower", axis="depth")
    return [ax], views, step


EXPLORATIONS = {
    "minting": explore_minting, "drive": explore_drive, "ledgers": explore_ledgers,
    "boundary": explore_boundary, "cascade": explore_cascade,
}
ORDER = ["minting", "drive", "ledgers", "boundary", "cascade"]


def assemble(explores, params, seed):
    axes, views, guided = [], [], []
    seen_ax = set()
    for name in [e for e in ORDER if e in explores]:
        ax_list, vs, step = EXPLORATIONS[name](params)
        for a in ax_list:
            if a.name not in seen_ax:
                axes.append(a); seen_ax.add(a.name)
        views.extend(vs); guided.append(step)
    meta = Meta(
        title="Character — finite-drive structure in driven-dissipative steady states",
        framing=[{"kind": "disclaimer", "text": "illustration, not evidence — every quantity is built in"},
                 {"kind": "note", "text": "the FDR view is estimator calibration, not a β-collapse test"},
                 {"kind": "note", "text": "observables live in the open interior; edges are approached, never evaluated"}],
        mode_default="guided", modes=("guided", "open"), guided=guided)
    return Scene(meta=meta, axes=axes, views=views,
                 provenance=dict(source="character", seed=seed, refine_factor=2,
                                 generated_at="<inject-at-boundary>"))


def main():
    ap = argparse.ArgumentParser(description="character scene source -> scene/v0.1")
    ap.add_argument("--explore", action="append", default=[],
                    choices=ORDER + ["all"], help="learner question(s); repeatable; 'all' = the full storyline")
    ap.add_argument("--cascade-depth", type=int, default=4)
    ap.add_argument("--drive-values", default="0,0.1,0.3,0.6,1.0")
    ap.add_argument("--seed", type=int, default=20260610)
    ap.add_argument("--emit", default=None, help="write scene JSON to this path (else stdout summary)")
    args = ap.parse_args()

    explores = ORDER if (not args.explore or "all" in args.explore) else args.explore
    params = dict(cascade_depth=args.cascade_depth,
                  drive_vals=[float(x) for x in args.drive_values.split(",")])
    scene = assemble(set(explores), params, args.seed)
    probs = validate(scene)
    if probs:
        print("SCENE INVALID:", *probs, sep="\n  "); sys.exit(1)
    if args.emit:
        with open(args.emit, "w", encoding="utf-8") as fh:
            fh.write(scene.to_json())
        print(f"wrote {args.emit}  ({len(scene.views)} views, {len(scene.axes)} axes, "
              f"{len(scene.meta.guided)} guided steps, mode_default={scene.meta.mode_default})")
    else:
        print(f"scene/v0.1: {len(scene.views)} views, {len(scene.axes)} axes, "
              f"guided steps: {[s.id for s in scene.meta.guided]}")
        for v in scene.views:
            print(f"  [{v.kind:9s}] {v.id:20s} {v.title}")


if __name__ == "__main__":
    main()
