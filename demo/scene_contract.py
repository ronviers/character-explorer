r"""scene_contract.py -- the general visualization handoff: schema `scene/v0.1`.

DOMAIN-NEUTRAL by design.  Nothing here mentions "character".  A *scene source* (any domain:
a dynamical system, a reaction network, a training run) computes its content and emits a Scene;
a general visualizer renders any Scene.  "character" is one source among future others.

The Python frozen dataclasses LOCK the shape (value semantics); the emitted JSON IS the wire
format.  A JS/Taichi visualizer mirrors these fields.  See
docs/architecture_scene_visualizer.md for the full design.

A Scene is:
  - meta    : title, framing/disclaimers, guided tour (ordered), and the available modes.
  - axes    : scrubbable parameter dimensions, PRE-SWEPT by the source (the visualizer runs no
              physics -- interactivity is scrubbing precomputed samples).
  - views   : typed panels (graph/series/locus/spectrum/hierarchy/sweep/readout) whose data are
              Channels.
  - channels: every graded value carries its convergence VERDICT (the NaN/refinement gate's
              result), so "honor the verdict" is a property of the general apparatus.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Any, Optional

SCHEMA = "scene/v0.1"

# convergence verdicts (the gate's vocabulary; carried to the pixel)
CONVERGED = "converged"               # finite, refinement-stable -> render as fact
BOUNDARY_TRIPWIRE = "boundary_tripwire"   # refinement-stable non-finite -> a degenerate face attained (falsification candidate); render as edge-state
UNCONVERGED = "unconverged"           # finite but drifts under refinement -> do NOT render as fact
FAKE_NAN_CLEARED = "fake_nan_cleared" # non-finite that vanished on refinement -> numerical artifact; do NOT render as fact
ANALYTIC = "analytic"                 # exact (no discretization to refine) -> render as fact
VERDICTS = {CONVERGED, BOUNDARY_TRIPWIRE, UNCONVERGED, FAKE_NAN_CLEARED, ANALYTIC}
TRUSTWORTHY = {CONVERGED, ANALYTIC}   # the visualizer renders only these as fact

VIEW_KINDS = {"graph", "series", "locus", "spectrum", "hierarchy", "sweep", "readout"}
MODES = {"guided", "open"}


@dataclass(frozen=True)
class Channel:
    """A graded datum: a value (or values indexed over axes) plus its convergence verdict.
    Scalar:        Channel(value=9.58, unit="nats", verdict=ANALYTIC)
    Axis-indexed:  Channel(over=["drive"], values=[0,0.04,0.40], verdict=CONVERGED)"""
    value: Optional[Any] = None
    values: Optional[list] = None
    over: Optional[list[str]] = None         # axis name(s) this channel is indexed by
    unit: Optional[str] = None
    verdict: str = ANALYTIC
    role: str = "primary"                     # primary | reference
    label: Optional[str] = None


@dataclass(frozen=True)
class Axis:
    """A scrubbable, PRE-SWEPT parameter dimension. `values` are the sampled settings."""
    name: str
    label: str                                # learner-facing question, e.g. "how hard is it driven?"
    values: list


@dataclass(frozen=True)
class View:
    """A typed panel.  `data` holds Channels and plain layout fields per the kind's schema."""
    kind: str                                 # one of VIEW_KINDS
    id: str
    title: str
    data: dict = field(default_factory=dict)
    explain: Optional[str] = None             # one-line "what am I looking at"


@dataclass(frozen=True)
class GuidedStep:
    """One ordered step of the guided tour (the default mode -- prevents early give-up)."""
    id: str
    title: str
    prompt: str                               # "turn frustration off -- where did the current go?"
    view: str                                 # View.id to focus
    axis: Optional[str] = None                # Axis.name to surface, if any


@dataclass(frozen=True)
class Meta:
    title: str
    framing: list = field(default_factory=list)        # [{kind:"disclaimer"|"note", text:...}]
    mode_default: str = "guided"                       # guided by default; toggle to open
    modes: tuple = ("guided", "open")
    guided: list = field(default_factory=list)         # ordered [GuidedStep,...]


@dataclass(frozen=True)
class Scene:
    meta: Meta
    axes: list = field(default_factory=list)           # [Axis,...]
    views: list = field(default_factory=list)          # [View,...]
    provenance: dict = field(default_factory=dict)
    schema: str = SCHEMA

    def to_dict(self) -> dict:
        return _clean(asdict(self))

    def to_json(self, indent: int = 2) -> str:
        # allow_nan=False -> strict JSON (JS JSON.parse-safe); non-finite values were already
        # mapped to None by _clean, so a stray NaN here is a bug worth surfacing, not emitting.
        return json.dumps(self.to_dict(), indent=indent, allow_nan=False)


def _clean(obj):
    """Recursively drop None-valued keys and map non-finite floats to None for a clean,
    strict-JSON wire format.  A boundary_tripwire's value is non-finite by nature -- the
    VERDICT carries the meaning, the numeric slot becomes null.  (asdict handles nested
    dataclasses inside list/dict fields, including Channels in View.data.)"""
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items() if v is not None}
    if isinstance(obj, list):
        return [_clean(v) for v in obj]
    if isinstance(obj, float) and not (obj == obj and abs(obj) != float("inf")):
        return None                                    # NaN or ±inf -> null
    return obj


def validate(scene: Scene) -> list[str]:
    """Cheap structural invariants; returns a list of problems (empty = ok)."""
    problems = []
    axis_names = {a.name for a in scene.axes}
    view_ids = {v.id for v in scene.views}
    if scene.schema != SCHEMA:
        problems.append(f"schema {scene.schema!r} != {SCHEMA!r}")
    if scene.meta.mode_default not in MODES:
        problems.append(f"mode_default {scene.meta.mode_default!r} not in {MODES}")
    for v in scene.views:
        if v.kind not in VIEW_KINDS:
            problems.append(f"view {v.id!r}: unknown kind {v.kind!r}")
        for ch in _channels_in(v.data):
            if ch.verdict not in VERDICTS:
                problems.append(f"view {v.id!r}: bad verdict {ch.verdict!r}")
            for ax in (ch.over or []):
                if ax not in axis_names:
                    problems.append(f"view {v.id!r}: channel over unknown axis {ax!r}")
            if ch.over and ch.values is None:
                problems.append(f"view {v.id!r}: axis-indexed channel missing `values`")
    for step in scene.meta.guided:
        if step.view not in view_ids:
            problems.append(f"guided step {step.id!r}: unknown view {step.view!r}")
        if step.axis and step.axis not in axis_names:
            problems.append(f"guided step {step.id!r}: unknown axis {step.axis!r}")
    return problems


def _channels_in(data):
    out = []
    def walk(o):
        if isinstance(o, Channel):
            out.append(o)
        elif isinstance(o, dict):
            for v in o.values():
                walk(v)
        elif isinstance(o, (list, tuple)):
            for v in o:
                walk(v)
    walk(data)
    return out


if __name__ == "__main__":
    # smoke test: build a tiny scene, validate, round-trip to JSON.
    sc = Scene(
        meta=Meta(
            title="smoke",
            framing=[{"kind": "disclaimer", "text": "illustration, not evidence"}],
            guided=[GuidedStep(id="s1", title="start", prompt="move the knob",
                               view="v1", axis="drive")],
        ),
        axes=[Axis(name="drive", label="how hard is it driven?", values=[0.0, 0.5, 1.0])],
        views=[View(kind="readout", id="v1", title="affinity",
                    data={"affinity": Channel(over=["drive"], values=[0.0, 4.8, 9.6],
                                              unit="nats", verdict=CONVERGED)})],
        provenance={"source": "smoke", "seed": 0},
    )
    probs = validate(sc)
    print("validate:", "OK" if not probs else probs)
    print(sc.to_json())
