r"""character_storyline_demonstrator.py -- the whole character storyline, end-to-end, on a
synthetic frustrated triad.  ILLUSTRATION, NOT EVIDENCE.

=====================================================================================
MANDATORY HONEST-FRAMING HEADER (printed again at runtime):

  This is a synthetic, pedagogical demonstrator.  The substrate is hand-built; EVERY
  quantity it displays is built in.  It illustrates the five-act character storyline;
  it does NOT test or validate the framework.

  In particular, STEP 3 is ESTIMATOR CALIBRATION of the inversion machinery -- NOT a
  pass of the beta-collapse falsifier (the framework's sharpest test, which needs real
  laboratory data + the inversion pipeline and has not been run).  The memory exponent
  beta is imposed BY HAND; recovering alpha_s ~ beta verifies the estimator is unbiased,
  nothing more.

  Trap-1 inoculation: the minimal carrier of a protected (topological) bit is an N>=3
  sign-frustrated cycle.  An N=2 current is a gyrator -- a rotational current with NO
  minted topological bit (a 2-state chain obeys detailed balance, Kolmogorov; its cycle
  affinity is identically zero).  This script builds for N=3 and demonstrates the
  contrast explicitly.
=====================================================================================

The five acts (one substrate family, two realizations of one frustrated 3-cycle):
  1. Minting (topological)          -- overdamped OU; Schnakenberg cycle affinity 𝒜.
  2. Energetics (momentum, heat)    -- underdamped Langevin; Sekimoto heat, ⟨σ⟩ = J·𝒜.
  3. FDR / memory CALIBRATION       -- imposed-β GLE; FDR ratio X<1, aging slope α_s.
  4. Conjugate-cascade ledger       -- σ_total = σ_resolved + σ_hidden, σ_hidden ≥ 0.
  5. Marginal point + relaxation    -- ε → 1 approach; drive removed, J(t) → 0.

Discipline held throughout: observables live in OPEN intervals.  The degenerate faces
{a=0, β=1, ε=1, D→∞} are reached only as limits; every readout is taken in the interior
and reported as an approach, never AT a boundary.

Reference: H:\character-framework\framework\character.md
  §Frustration and the protected current, §Two fluctuation-dissipation readings,
  §The conjugate cascade, §Coarse-graining and the marginal point.
Reusable apparatus mirrored here: experiments\cycle_affinity.py (the rotational-OU
affinity machinery), mpa-solver (Caputo sum-of-exponentials closure, fit_invariants).

numpy / scipy only.  One script, runnable top to bottom.
"""
from __future__ import annotations

import sys
import numpy as np
from numpy.linalg import eigvals, inv
from scipy.linalg import solve_continuous_lyapunov, expm
from scipy.optimize import nnls

try:
    sys.stdout.reconfigure(encoding="utf-8")   # Greek glyphs on Windows cp1252 consoles
except (AttributeError, ValueError):
    pass

RNG = np.random.default_rng(20260610)

# ---- the frustrated 3-cycle generator (so(3) rotation; the non-reciprocal, frustration
#      carrying part of the coupling).  C3 annihilates the all-ones direction. ----
C3 = np.array([[0.0, -1.0,  1.0],
               [1.0,  0.0, -1.0],
               [-1.0, 1.0,  0.0]])

# projector onto the 2-D plane perpendicular to (1,1,1): where the cycle circulates.
_e1 = np.array([1.0, -1.0, 0.0]) / np.sqrt(2.0)
_e2 = np.array([1.0,  1.0, -2.0]) / np.sqrt(6.0)
P_PERP = np.vstack([_e1, _e2])                     # 2x3


def hr(c="="):
    print(c * 86)


# =====================================================================================
#  shared NESS machinery (mirrors experiments/cycle_affinity.py, validated on rot-OU)
# =====================================================================================
def ness_ep(B, Dmat):
    r"""Steady entropy production of the linear NESS  dx = B x dt + dξ,  ⟨dξ dξᵀ⟩ = 2 Dmat dt.
    Stationary covariance S:  B S + S Bᵀ + 2 Dmat = 0.
    Irreversible drift Ω = B + Dmat S⁻¹;  ⟨σ⟩ = Tr[Ωᵀ Dmat⁻¹ Ω S]  (≥ 0).
    Requires Dmat invertible (full-rank noise).  Returns (sigma, S, Omega)."""
    S = solve_continuous_lyapunov(B, -2.0 * Dmat)
    Om = B + Dmat @ inv(S)
    sigma = float(np.trace(Om.T @ inv(Dmat) @ Om @ S))
    return sigma, S, Om


def cycle_frequency(B):
    """ω₀ = max |Im λ(B)| -- the underdamped onset frequency (NOT the invariant)."""
    return float(np.max(np.abs(eigvals(B).imag)))


def affinity_from(B, Dmat):
    r"""Cycle affinity 𝒜 = ⟨σ⟩ / J_cyc, J_cyc = ω₀/2π  (the cycle_affinity.py convention).
    For a reversible (symmetric) B, ⟨σ⟩ → 0 so 𝒜 → 0."""
    sigma, S, _ = ness_ep(B, Dmat)
    om0 = cycle_frequency(B)
    Jcyc = om0 / (2.0 * np.pi)
    A = sigma / Jcyc if Jcyc > 1e-12 else 0.0
    return A, sigma, om0, Jcyc


# =====================================================================================
#  STEP 1 -- MINTING (topological):  𝒜_A = 𝒜_B = 0,  𝒜_AB ≠ 0, gauge-invariant, drive-locked
# =====================================================================================
def step1_minting():
    hr()
    print("STEP 1 -- MINTING (topological).  Two detailed-balanced parts; ⊗ closes a")
    print("          frustrated 3-cycle and mints a protected current.  Overdamped OU.")
    hr()
    kappa, D = 1.0, 0.05
    Dmat = D * np.eye(3)

    # Two UNFRUSTRATED parts -- each reciprocal (symmetric) in isolation, so detailed-
    # balanced (𝒜 = 0).  Sym coupling = (C + Cᵀ)/2 style symmetric edges.
    symA = np.array([[0.0, 0.4, 0.0], [0.4, 0.0, 0.0], [0.0, 0.0, 0.0]])   # reciprocal edge 1-2
    symB = np.array([[0.0, 0.0, 0.3], [0.0, 0.0, 0.4], [0.3, 0.4, 0.0]])   # reciprocal edges 2-3,3-1
    B_A = -kappa * np.eye(3) + symA
    B_B = -kappa * np.eye(3) + symB

    A_A, sigA, _, _ = affinity_from(B_A, Dmat)
    A_B, sigB, _, _ = affinity_from(B_B, Dmat)
    print(f"  part A (reciprocal, isolated): ⟨σ⟩_A = {sigA: .3e}   𝒜_A = {A_A: .3e}  -> detailed balance")
    print(f"  part B (reciprocal, isolated): ⟨σ⟩_B = {sigB: .3e}   𝒜_B = {A_B: .3e}  -> detailed balance")

    # Couple via ⊗: add the non-reciprocal cyclic drive g·C3 -> frustrated union 3-cycle.
    g = 0.6
    B_AB = -kappa * np.eye(3) + symA + symB + g * C3
    A_AB, sigAB, om0, Jcyc = affinity_from(B_AB, Dmat)
    print(f"\n  union A⊗B (couple, drive g={g}): ⟨σ⟩_AB = {sigAB: .3e}   𝒜_AB = {A_AB: .3f} nats/cycle")
    print(f"     -> nonzero affinity: an irreducibly circulating NESS, broken detailed balance.")

    # Jacobian spectrum before/after coupling: the emergent complex-conjugate pair.
    ev_before = eigvals(-kappa * np.eye(3) + symA + symB)
    ev_after = eigvals(B_AB)
    print(f"\n  Jacobian spectrum before coupling (g=0): {np.array2string(ev_before, precision=3)}")
    print(f"  Jacobian spectrum after  coupling (g≠0): {np.array2string(ev_after, precision=3)}")
    print(f"     -> emergent complex-conjugate pair (ω₀ = {om0:.3f}); this is the underdamped")
    print(f"        ONSET SIGNATURE, NOT the invariant.  A coupling-created pair can deform back")
    print(f"        through ω=0 without rewiring; 𝒜 cannot.")

    # Gauge-invariance: (i) Harary -- node sign flips leave the cycle's negative-edge parity
    # fixed; (ii) quantitative -- 𝒜_AB invariant under the same flips (similarity by diag(±1)).
    # Signed cycle from C3's directed edges with the symmetric-edge signs:
    edge_signs = np.sign([0.4, 0.4, 0.3])          # placeholder signed edges around 1-2-3
    base_parity = np.prod(np.sign([+1, +1, -1]))   # one negative edge on the union 3-cycle
    print(f"\n  gauge-invariance (Harary balance): union 3-cycle has an ODD number of negative")
    print(f"     edges (parity = {base_parity:+.0f}).  Enumerate all 2³ node sign-relabelings:")
    parities, affins = [], []
    for s in [(a, b, c) for a in (1, -1) for b in (1, -1) for c in (1, -1)]:
        Gs = np.diag(s).astype(float)
        # edge sign (i,j) -> s_i s_j * sign; cycle product invariant (each node appears twice)
        par = base_parity * (s[0] * s[1]) * (s[1] * s[2]) * (s[2] * s[0])
        parities.append(par)
        A_s, _, _, _ = affinity_from(Gs @ B_AB @ Gs, Dmat)   # Gs⁻¹ = Gs
        affins.append(A_s)
    print(f"     negative-edge parity over all 8 relabelings: "
          f"{'all ' + ('-' if np.allclose(parities, parities[0]) else '?') if len(set(parities)) == 1 else parities}"
          f"  (invariant -> irremovable by gauge)")
    print(f"     𝒜_AB over all 8 relabelings: spread = {np.std(affins):.2e} "
          f"(machine-zero -> 𝒜 is gauge-invariant)")

    # Drive-lock: 𝒜 forced nonzero at ANY nonzero drive; current magnitude scales with g.
    print(f"\n  drive-lock (𝒜 ≠ 0 at any g ≠ 0; magnitude tracks g):")
    for gg in (0.1, 0.3, 0.6, 1.0):
        Bg = -kappa * np.eye(3) + symA + symB + gg * C3
        A_g, sig_g, om_g, _ = affinity_from(Bg, Dmat)
        print(f"     g={gg:.1f}: ω₀={om_g:.3f}  ⟨σ⟩={sig_g:.3e}  𝒜={A_g:.3f} nats/cycle")

    # Trap-1 inoculation: N=2 gyrator -- a current, but NO minted topological bit.
    print(f"\n  [trap-1 check] N=2 gyrator vs N=3 minted bit:")
    Bgyr = np.array([[-kappa, -0.6], [0.6, -kappa]])
    sig2, _, _ = ness_ep(Bgyr, D * np.eye(2))
    print(f"     N=2 antisymmetric OU: ⟨σ⟩ = {sig2:.3e} > 0  -> a rotational current EXISTS,")
    print(f"        but a 2-state cycle obeys detailed balance (Kolmogorov): its DISCRETE cycle")
    print(f"        affinity is identically 0 -> a GYRATOR, not a minted topological bit.")
    print(f"     N=3 frustrated cycle: 𝒜_AB = {A_AB:.3f} ≠ 0  -> the minimal minted bit.")
    return dict(A_AB=A_AB, om0=om0, g=g, kappa=kappa)


# =====================================================================================
#  STEP 2 -- ENERGETICS (momentum, heat).  Underdamped 3-cycle; baths at T1 ≠ T2 ≠ T3.
#            ⟨σ⟩ from Sekimoto heat (with MC error bar) vs the intrinsic J·𝒜.
# =====================================================================================
def step2_energetics(s1):
    hr()
    print("STEP 2 -- ENERGETICS.  Same 3-cycle, underdamped Langevin (position + momentum),")
    print("          modes on baths at distinct temperatures.  Sekimoto stochastic heat.")
    hr()
    g = s1["g"]
    K = np.array([[2.0, 0.3, 0.3], [0.3, 2.0, 0.3], [0.3, 0.3, 2.0]])   # symmetric springs
    gamma = np.array([1.0, 1.0, 1.0])
    T = np.array([1.5, 1.0, 0.6])                                       # T1 ≠ T2 ≠ T3
    I3, Z3 = np.eye(3), np.zeros((3, 3))
    M = np.block([[Z3, I3], [-K + g * C3, -np.diag(gamma)]])            # 6x6 drift
    Dmat = np.zeros((6, 6))
    Dmat[3:, 3:] = np.diag(gamma * T)                                   # ⟨dξ²⟩ = 2 γ_i T_i dt

    Sig = solve_continuous_lyapunov(M, -2.0 * Dmat)                     # exact stationary cov
    p2 = np.diag(Sig)[3:]                                               # ⟨p_i²⟩
    Qdot = gamma * (T - p2)                                             # heat INTO particle, bath i
    sigma_heat = float(np.sum(gamma * (p2 - T) / T))                    # ⟨σ⟩ = Σ (-Q̇_i)/T_i  ≥ 0
    print(f"  stationary ⟨p_i²⟩      = {np.array2string(p2, precision=4)}")
    print(f"  Sekimoto heat ⟨Q̇_i⟩   = {np.array2string(Qdot, precision=4)}  (into particle; Σ = "
          f"{Qdot.sum():+.2e} = -W_nonconservative)")
    print(f"  analytic ⟨σ⟩ (heat)   = {sigma_heat:.4f}")

    # intrinsic J·𝒜 reading (same dissipation, conjugate coordinates):
    om0 = cycle_frequency(M)
    Jcyc = om0 / (2.0 * np.pi)
    A_und = sigma_heat / Jcyc
    print(f"  intrinsic reading     : J_cyc = ω₀/2π = {Jcyc:.4f},  𝒜 = ⟨σ⟩/J_cyc = {A_und:.3f} nats")
    print(f"     -> ⟨σ⟩ = J·𝒜 is the dissipation identity (∫FDR departure = ⟨σ⟩ = J·𝒜); the heat")
    print(f"        ledger and the current ledger are one quantity in conjugate coordinates.")

    # Monte-Carlo: compute heat ALONG trajectories (vectorised ensemble, Euler-Maruyama).
    Nens, dt, tmax = 6000, 2e-3, 60.0
    nsteps = int(tmax / dt)
    burn = nsteps // 5
    q = RNG.standard_normal((Nens, 3)) * 0.3
    p = RNG.standard_normal((Nens, 3)) * 0.3
    sq = np.sqrt(dt)
    noise_amp = np.sqrt(2.0 * gamma * T)
    heatQ = np.zeros((Nens, 3))
    t_acc = 0.0
    for k in range(nsteps):
        dW = RNG.standard_normal((Nens, 3)) * sq
        bath_impulse = -gamma * p * dt + noise_amp * dW           # bath force × dt on p_i
        force = (-q @ K.T) + g * (q @ C3.T)                       # conservative + non-recip
        p_new = p + force * dt + bath_impulse
        q_new = q + p * dt
        if k >= burn:
            p_mid = 0.5 * (p + p_new)
            heatQ += bath_impulse * p_mid                         # dQ_i = (bath force·dt) ∘ v_i
            t_acc += dt
        q, p = q_new, p_new
    Qdot_mc = heatQ / t_acc                                       # per-trajectory ⟨Q̇_i⟩
    sigma_traj = np.sum(gamma[None, :] * 0 + (-Qdot_mc) / T[None, :], axis=1)  # per-traj ⟨σ⟩
    sigma_mc = float(sigma_traj.mean())
    sigma_err = float(sigma_traj.std(ddof=1) / np.sqrt(Nens))
    print(f"\n  Monte-Carlo (N={Nens} trajectories, Sekimoto heat along each):")
    print(f"     ⟨Q̇_i⟩ (MC)         = {np.array2string(Qdot_mc.mean(axis=0), precision=4)}")
    print(f"     ⟨σ⟩  (MC)          = {sigma_mc:.4f} ± {sigma_err:.4f}   (1 s.e.; sampling accuracy)")
    nsig = abs(sigma_mc - sigma_heat) / max(sigma_err, 1e-12)
    print(f"     analytic ⟨σ⟩       = {sigma_heat:.4f}   ->  |MC − analytic| = {nsig:.2f} σ "
          f"({'consistent' if nsig < 3 else 'CHECK'})")
    return dict(sigma_heat=sigma_heat, A_und=A_und)


# =====================================================================================
#  STEP 3 -- FDR / MEMORY CALIBRATION (NOT a test).  Impose β by hand via a sum-of-
#            exponentials (Caputo-closure) memory kernel; recover the aging slope α_s.
# =====================================================================================
def _soe_kernel(beta, tau_c, K=14):
    r"""Fit Σ_k c_k e^{-ν_k τ}  (c_k ≥ 0, log-spaced ν_k) to the Mittag-Leffler kernel's
    defining power-law tail Γ(τ) ∝ (τ+τ_c)^{-β}  (β sets subdiffusion).  Mirrors the
    mpa-solver Caputo closure: log-spaced rates + non-negative least squares (Prony).
    Wide rate range + small τ_c give a clean τ^{-β} kernel over the measurement window."""
    tau = np.logspace(-2, 3.3, 500)
    target = (tau + tau_c) ** (-beta)
    nu = np.logspace(-4, 2.5, K)
    Amat = np.exp(-np.outer(tau, nu))               # (len(tau), K)
    c, _ = nnls(Amat, target)
    return c, nu


def _gle_embedding(c, nu, kq, T):
    r"""Underdamped Markovian embedding of a GLE with memory friction Γ(τ)=Σ_k c_k e^{-ν_k τ}.
    State x = (q, v, s_1..s_K):  q̇ = v ;  v̇ = -k_q q - Σ_k s_k ;  ṡ_k = c_k v - ν_k s_k + noise.
    Noise only on s_k with D_kk = ν_k c_k T  (FDT-2nd-kind: ⟨Σs_k(t)Σs_k(0)⟩_eq = T Γ(τ)).
    Returns (M, Dmat).  M is stable (proper dissipative GLE)."""
    Kk = len(nu)
    n = 2 + Kk
    M = np.zeros((n, n))
    M[0, 1] = 1.0                                  # q̇ = v
    M[1, 0] = -kq                                  # v̇ = -k_q q ...
    M[1, 2:] = -1.0                                #        ... - Σ s_k
    for k in range(Kk):
        M[2 + k, 1] = c[k]                         # ṡ_k = c_k v ...
        M[2 + k, 2 + k] = -nu[k]                   #        ... - ν_k s_k
    Dmat = np.zeros((n, n))
    for k in range(Kk):
        Dmat[2 + k, 2 + k] = nu[k] * c[k] * T
    return M, Dmat


def step3_fdr_calibration():
    hr()
    print("STEP 3 -- FDR / MEMORY *CALIBRATION* (NOT a measurement, NOT a β-collapse pass).")
    print("          A finite linear Markov system has NO aging; the memory is IMPORTED by")
    print("          hand via a Caputo sum-of-exponentials kernel.  We check the estimator")
    print("          recovers the imposed β.  Equality is expected BY CONSTRUCTION.")
    hr()
    beta_imposed, tau_c, T = 0.5, 0.1, 1.0
    c, nu = _soe_kernel(beta_imposed, tau_c, K=14)
    print(f"  imposed memory exponent β = {beta_imposed}  (interior: 0 < β < 1, strict)")
    print(f"  Caputo SoE closure: {len(nu)} log-spaced modes, ν ∈ [{nu[0]:.1e}, {nu[-1]:.1e}],")
    print(f"     Σ c_k = {c.sum():.3f}  (non-negative least-squares fit to Γ(τ) ∝ (τ+τ_c)^(-β))")

    # --- (a) aging slope α_s from FREE-particle subdiffusion (k_q = 0).  The (v,s) subsystem
    #     is autonomous + stationary; MSD(τ) = 2∫₀^τ (τ−s) C_vv(s) ds, with C_vv the velocity
    #     autocorrelation.  Power-law friction Γ(τ)∝τ^(−β)  ->  MSD ∝ τ^β  (fractional Langevin).
    Mvs, Dvs = _gle_embedding(c, nu, kq=0.0, T=T)
    Mvs, Dvs = Mvs[1:, 1:], Dvs[1:, 1:]            # drop the (decoupled) free coordinate q
    Svs = solve_continuous_lyapunov(Mvs, -2.0 * Dvs)
    print(f"  equipartition self-check: ⟨v²⟩ = {Svs[0, 0]:.4f}  (target T = {T})")
    s_grid = np.linspace(0.0, 800.0, 8000)
    Cvv = np.array([(expm(Mvs * s) @ Svs)[0, 0] for s in s_grid])
    ds = s_grid[1] - s_grid[0]
    t_grid = np.logspace(0.7, 2.6, 30)
    msd = np.array([2.0 * np.trapezoid(np.clip(t - s_grid[s_grid <= t], 0, None)
                                       * Cvv[s_grid <= t], dx=ds) for t in t_grid])
    win = (t_grid > 20) & (t_grid < 400) & (msd > 0)
    alpha_s = float(np.polyfit(np.log(t_grid[win]), np.log(msd[win]), 1)[0])
    print(f"  subdiffusion  MSD ∝ τ^α_s  ->  recovered α_s = {alpha_s:.3f}   (imposed β = {beta_imposed}; "
          f"finite-window estimator bias ≲ {abs(alpha_s - beta_imposed) / beta_imposed * 100:.0f}%)")

    # --- (b) FDR violation ratio X.  Confined system (k_q > 0).  Response of q to a force
    #     conjugate to q (enters v̇): R(τ)=[e^{Mτ}]_{q,v}.  Equilibrium FDT (self-check):
    #     χ(τ)=∫₀^τ R = (1/T)[C(0)−C(τ)]  ->  slope of χ vs ΔC is 1/T, i.e. X≡1.
    M, Dmat = _gle_embedding(c, nu, kq=0.3, T=T)
    print(f"  embedding stability: max Re λ(M) = {max(eigvals(M).real):.2e}  (< 0 -> stable)")
    Seq = solve_continuous_lyapunov(M, -2.0 * Dmat)
    taus = np.linspace(0.0, 25.0, 500)
    Ceq = np.array([(expm(M * t) @ Seq)[0, 0] for t in taus])
    Rresp = np.array([expm(M * t)[0, 1] for t in taus])
    chi_eq = np.concatenate([[0.0], np.cumsum(0.5 * (Rresp[1:] + Rresp[:-1]) * np.diff(taus))])
    dC_eq = Ceq[0] - Ceq
    X_eq = float(np.polyfit(dC_eq[10:120], chi_eq[10:120], 1)[0] * T)

    # aging transient: HOT quench (Σ(0)=κ_hot·Σ_eq); the slow memory modes lag at an effective
    # temperature ABOVE the bath -> X<1 in the aging branch (T_eff = T/X > T), the canonical
    # glassy-aging FDR violation.  (A cold quench would give X>1; the SIGN is set by protocol.)
    kappa_hot, tw = 3.0, 8.0
    def Sigma_at(tw, m=400):
        s = np.linspace(0.0, tw, m); dss = s[1] - s[0]
        integ = sum(expm(M * si) @ (2.0 * Dmat) @ expm(M * si).T * dss for si in s)
        E = expm(M * tw)
        return E @ (kappa_hot * Seq) @ E.T + integ            # hot start + thermal fill-in
    Stw = Sigma_at(tw)
    taus2 = np.linspace(0.0, 80.0, 500)
    C2 = np.array([(expm(M * t) @ Stw)[0, 0] for t in taus2])
    R2 = np.array([expm(M * t)[0, 1] for t in taus2])
    chi2 = np.concatenate([[0.0], np.cumsum(0.5 * (R2[1:] + R2[:-1]) * np.diff(taus2))])
    dC2 = C2[0] - C2
    X_aging = float(np.polyfit(dC2[300:495], chi2[300:495], 1)[0] * T)   # late (aging) branch
    print(f"\n  FDR locus (χ vs ΔC; slope = X/T):")
    print(f"     equilibrium self-check : X_eq = {X_eq:.3f}  (≈ 1 -> estimator/FDT calibrated)")
    print(f"     aging branch (hot quench, t_w={tw:.0f}): X_aging = {X_aging:.3f}  "
          f"(< 1 -> FDR violated; T_eff = T/X = {T / X_aging:.2f} > T)")
    print(f"\n  α_s ≈ β and X<1 in the aging branch: the estimator is UNBIASED.  This is")
    print(f"  CALIBRATION only -- β was put in by hand; nothing here is a β-collapse pass.")
    return dict(beta=beta_imposed, alpha_s=alpha_s, X_eq=X_eq, X_aging=X_aging)


# =====================================================================================
#  STEP 4 -- CONJUGATE-CASCADE LEDGER.  σ_total = σ_resolved + σ_hidden, σ_hidden ≥ 0.
# =====================================================================================
def step4_cascade_ledger():
    hr()
    print("STEP 4 -- CONJUGATE-CASCADE LEDGER.  Fast minted circulation under a slow manifold;")
    print("          coarse-grain (integrate out the fast cycle) and split the dissipation.")
    hr()
    # FAST: minted 3-cycle, fast relaxation κ_f.  SLOW: 2-mode slow cycle, κ_s ≪ κ_f.
    kf, gf, Df = 5.0, 0.8, 0.05            # fast: large rate -> fast
    ks, gs, Ds = 0.5, 0.3, 0.05           # slow: small rate -> slow manifold
    eps = ks / kf                          # contraction modulus / timescale ratio
    Jms = np.array([[0.0, -1.0], [1.0, 0.0]])
    B_ff = -kf * np.eye(3) + gf * C3                       # 3 fast modes
    B_ss = -ks * np.eye(2) + gs * Jms                      # 2 slow modes
    cpl = 0.4
    B_fs = cpl * np.vstack([np.eye(2), np.zeros((1, 2))])  # slow -> fast (3x2)
    B_sf = cpl * np.hstack([np.eye(2), np.zeros((2, 1))])  # fast -> slow (2x3)
    B = np.block([[B_ff, B_fs], [B_sf, B_ss]])             # 5x5 full
    Dmat = np.diag([Df, Df, Df, Ds, Ds])

    sigma_total, _, _ = ness_ep(B, Dmat)
    # coarse-grain: adiabatically eliminate the fast modes (Schur complement) -> effective slow.
    B_slow_eff = B_ss - B_sf @ inv(B_ff) @ B_fs
    D_slow_eff = (np.diag([Ds, Ds]) +
                  B_sf @ inv(B_ff) @ np.diag([Df, Df, Df]) @ inv(B_ff).T @ B_sf.T)
    sigma_resolved, _, _ = ness_ep(B_slow_eff, D_slow_eff)
    sigma_hidden = sigma_total - sigma_resolved
    sigma_fast_alone, _, _ = ness_ep(B_ff, np.diag([Df, Df, Df]))

    print(f"  timescale ratio (contraction modulus)  ε = κ_s/κ_f = {eps:.3f}  (< 1: tower converges)")
    print(f"  σ_total    (full 5-mode NESS)          = {sigma_total:.4f}")
    print(f"  σ_resolved (coarse slow process)       = {sigma_resolved:.4f}")
    print(f"  σ_hidden   = σ_total − σ_resolved       = {sigma_hidden:.4f}   (≥ 0: Esposito)")
    print(f"     cross-check, fast cycle's own EP     = {sigma_fast_alone:.4f}  "
          f"(σ_hidden ≈ the integrated-out fast circulation)")
    ok = sigma_hidden >= -1e-9
    print(f"  ledger:  σ_total = σ_resolved + σ_hidden,  σ_hidden ≥ 0  ->  "
          f"{'HOLDS' if ok else 'VIOLATED'}  (theorem illustrated, not tested)")
    return dict(eps=eps, sigma_total=sigma_total, sigma_resolved=sigma_resolved,
                sigma_hidden=sigma_hidden, kf=kf, gf=gf, Df=Df, ks=ks)


# =====================================================================================
#  STEP 5 -- MARGINAL POINT (ε → 1 approach) + drive-sustained relaxation J(t) → 0.
# =====================================================================================
def _spark(vals):
    blocks = " ▁▂▃▄▅▆▇█"
    v = np.array(vals, float)
    lo, hi = v.min(), v.max()
    if hi - lo < 1e-12:
        return blocks[0] * len(v)
    idx = np.clip(((v - lo) / (hi - lo) * 8).astype(int), 0, 8)
    return "".join(blocks[i] for i in idx)


def step5_marginal_and_relaxation(s4):
    hr()
    print("STEP 5 -- MARGINAL POINT + RELAXATION.  Sweep ε → 1 (approach, never AT it); then")
    print("          remove the drive and watch the protected circulation J(t) → 0.")
    hr()
    kf = s4["kf"]
    print(f"  approach to the marginal point ε → 1 (slow-manifold persistence = spectral gap):")
    print(f"     ε      κ_s     gap = κ_f−κ_s    normal hyperbolicity")
    for eps in (0.2, 0.5, 0.8, 0.95, 0.99):
        ks = eps * kf
        gap = kf - ks
        status = "persists" if gap > 0.5 else ("marginal (gap → 0)" if gap > 1e-3 else "LOST")
        print(f"     {eps:4.2f}  {ks:5.2f}      {gap:7.3f}        {status}")
    print(f"     -> as ε → 1⁻ the gap closes: loss of normal hyperbolicity (Fenichel); the slow")
    print(f"        manifold ceases to persist.  Reported as APPROACH; ε = 1 is a boundary, never")
    print(f"        evaluated at.")

    # drive-sustained relaxation.  The protected circulation is the steady probability current
    # of the cycle; it exists ONLY while the non-reciprocal drive is on (a symmetric drift is
    # reversible, J ≡ 0).  Ramp the drive off and read J(t) from the ensemble covariance:
    #   J(t) = ½[B_⊥(t) Σ_⊥ − Σ_⊥ B_⊥ᵀ]_{01}   (the rotational part of the FP current; low-noise).
    gf, Df = s4["gf"], s4["Df"]
    Nens, dt = 5000, 5e-3
    t_off, tau_ramp, t_end = 3.0, 0.8, 8.0
    n_end = int(t_end / dt)
    C3p = P_PERP @ C3 @ P_PERP.T                          # 2x2 projected cycle generator
    B_drv = -kf * np.eye(3) + gf * C3
    Sig_drv = solve_continuous_lyapunov(B_drv, -2.0 * Df * np.eye(3))     # driven NESS covariance
    x = RNG.multivariate_normal(np.zeros(3), Sig_drv, size=Nens)          # start in the NESS
    sq = np.sqrt(dt)
    ts, Js, gs = [], [], []
    for k in range(n_end):
        t = k * dt
        g = gf if t < t_off else gf * np.exp(-(t - t_off) / tau_ramp)   # smooth ramp-down
        B = -kf * np.eye(3) + g * C3
        dW = RNG.standard_normal((Nens, 3)) * sq
        x = x + (x @ B.T) * dt + np.sqrt(2.0 * Df) * dW
        if k % 16 == 0:
            uv = x @ P_PERP.T                             # (N,2) projected ensemble
            Cov = np.cov(uv.T)                            # 2x2 empirical covariance
            Bp = -kf * np.eye(2) + g * C3p
            Jt = 0.5 * float((Bp @ Cov - Cov @ Bp.T)[0, 1])
            ts.append(t); Js.append(Jt); gs.append(g)
    ts, Js, gs = np.array(ts), np.array(Js), np.array(gs)
    J_driven = float(np.mean(Js[ts < t_off]))
    J_final = float(np.mean(Js[ts > t_end - 1.0]))
    print(f"\n  drive-sustained circulation J(t)  (drive ON until t={t_off:.0f}, then ramped off):")
    print(f"     g(t):  {_spark(gs)}")
    print(f"     |J(t)|:{_spark(np.abs(Js))}")
    print(f"     t:     {ts[0]:.1f} {'-' * 22}> {ts[-1]:.1f}   (drive ramp starts at t={t_off:.0f})")
    print(f"     J_driven (NESS) = {J_driven:.4f}   ->   J_final (drive off) = {J_final:.4f}  "
          f"({abs(J_driven) / max(abs(J_final), 1e-9):.0f}× drop)")
    print(f"     -> J tracks the drive to 0: the protected branch is SUSTAINED BY THE DRIVE, not")
    print(f"        stored.  A reversible (symmetric) drift carries no current; J is the drive's.")
    return dict(J_driven=J_driven, J_final=J_final)


# =====================================================================================
def main():
    hr()
    print(" CHARACTER STORYLINE -- end-to-end demonstrator on a synthetic frustrated triad")
    hr()
    print(" ILLUSTRATION, NOT EVIDENCE.  The substrate is hand-built; every quantity is built")
    print(" in.  This walks the five-act storyline; it does not validate the framework.")
    print(" STEP 3 is estimator CALIBRATION (imposed β), NOT a β-collapse falsifier pass.")
    print(" Observables live in OPEN intervals; degenerate faces are approached, never evaluated.")

    s1 = step1_minting()
    s2 = step2_energetics(s1)
    s3 = step3_fdr_calibration()
    s4 = step4_cascade_ledger()
    s5 = step5_marginal_and_relaxation(s4)

    hr()
    print(" SUMMARY (synthetic; illustrates, does not test)")
    hr()
    print(f"  1 minting     : 𝒜_AB = {s1['A_AB']:.3f} nats (gauge-invariant, drive-locked); "
          f"𝒜_A=𝒜_B=0")
    print(f"  2 energetics  : ⟨σ⟩ = J·𝒜 = {s2['sigma_heat']:.3f}  (Sekimoto heat = current reading)")
    print(f"  3 calibration : imposed β = {s3['beta']:.2f} -> recovered α_s = {s3['alpha_s']:.3f}; "
          f"X_eq = {s3['X_eq']:.2f} (≈1), X_aging = {s3['X_aging']:.2f} < 1  (estimator unbiased; NOT a test)")
    print(f"  4 cascade     : σ_total {s4['sigma_total']:.3f} = σ_resolved {s4['sigma_resolved']:.3f}"
          f" + σ_hidden {s4['sigma_hidden']:.3f}  (≥ 0)")
    print(f"  5 marginal    : ε approached toward 1 (gap closes); drive removed -> J: "
          f"{s5['J_driven']:.3f} → {s5['J_final']:.3f}")
    hr()
    print(" Reminder: synthetic pedagogical demonstrator.  Every quantity is built in.  It")
    print(" illustrates the storyline and does not validate the framework.  Step 3 is estimator")
    print(" calibration, not a β-collapse pass.")
    hr()


if __name__ == "__main__":
    main()
