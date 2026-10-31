"""Reference-vs-fast checks.  [CONTRACT: Case / Pair / pair registry + checks]

Registering a pair (anyone, in correctness/test_<topic>.py):

    @pair("moe.loop")                                  # fp32, tolerances from TOLERANCES
    @pair("moe.loop", tol=1e-5, grad_tol=1e-4)         # or your own, < 1e-2 for fp32
    @pair("model.bf16", dtype=torch.bfloat16)          # fast inputs cast to bf16 (or the fast fn runs autocast)
    def _(device):
        ...
        return Case(ref=ref_fn, fast=fast_fn, inputs=[x], params_ref=[...], params_fast=[...])

Rules: the reference is written independently from the definition, in fp64, never by calling the
fast code. fp32 tolerances < 1e-2 always (so a 1.01 error fails).

  * rel_err(fast, ref) = ||fast - ref|| / ||ref|| in fp64; AssertionError on shape mismatch or NaN/Inf.
  * check(pair, device, fast_override=None): build the Case; clone the inputs (fp64 for ref, pair.dtype for
    fast); compare every output; backpropagate the SAME seeded random cotangent through both, in one backward
    per side (a custom backward such as the reversible stack runs once); compare the grads of inputs that
    require grad and of params_fast vs params_ref (a None grad counts as zeros: an MoE expert with no tokens).
    AssertionError naming the pair, the tensor, the error and the tolerance. Returns {name: error}, and
    records the worst errors in RESULTS (conftest prints them at the end of the run).
  * scaled(k=1.01): returns a wrapper factory; check applies fast_override(case.fast). Outputs * k.
  * determinism (Task 3 of G6_Team_Task_Plan.md, decision D02): after the parity checks, check() runs the fast
    side a SECOND time on fresh copies of the same inputs, with the same cotangent, and requires the outputs
    and the gradients to be bit-identical (torch.equal). The parity tolerance cannot see this: a kernel that
    is wrong by 1e-9 from run to run passes parity but breaks reproducible training and the 5% repeat check.
    A pair whose fast code is non-deterministic by design (CUDA atomics, e.g. an index_add_ scatter) opts out
    with @pair(..., deterministic=False) and says why in a comment. The 1.01 drill (fast_override) skips it.
Do not use torch.allclose defaults: in bf16 (rtol 1.6e-2) they let a 1% error pass.

Precision (TOLERANCES, measured on the full lab_small model, correctness/test_model.py):
  fp32  clean errors: outputs <= 3e-7, gradients <= 1.9e-5 (after 30 training steps). A KE bug that changes
        the embedding by 6e-5 shows 9e-6 in the logits but 1.2e-4 in the gradients: so outputs 1e-5,
        gradients 5e-5. These pairs are in the 1.01 drill (test_framework.py). model.lab_small.chunked uses 1e-4:
        its ln_f gradient is an fp32 sum over the 131072-token vocabulary (6.2e-5, test_model.py).
  bf16  lab_small under CPU bf16 autocast, MoE routing replayed (test_model.py), T = 64 and 512 alike: outputs
        3.8e-3, gradients <= 1.3e-2 (router; attention and LayerNorm ~1e-2, experts 8e-3). So outputs 1e-2,
        gradients 3e-2. Without the replay a few tokens change experts and expert gradients are off by up to
        26%. A bf16 tolerance cannot catch a 1% error, so bf16 pairs are NOT in the 1.01 drill; they catch
        large bf16 regressions.
        Measured again on an A100-SXM4-40GB (torch 2.11, CUDA 13.0, 27 Oct): model.lab_small.bf16 outputs 4.1e-3,
        gradients 9.4e-3; moe.loop.bf16 4.9e-3 / 5.8e-3; fp32 pairs at most 4.1e-7 / 1.4e-6. All inside the
        tolerances above with 2.4x (bf16 outputs) to 37x (fp32 gradients) to spare.
  fp8   no fp8 code yet. Add an entry here, with the measurement, when an fp8 path exists.
"""
from __future__ import annotations

import copy
import math
from dataclasses import dataclass, field
from typing import Any, Callable

import torch

PAIRS: dict = {}
RESULTS: dict = {}                   # pair name -> worst errors of its last clean check (conftest prints it)
DRILL_TOL = 1e-2                     # a pair with both tolerances below this must fail the 1.01 drill
TOLERANCES = {                       # fast dtype -> (outputs, gradients)
    torch.float32: (1e-5, 5e-5),
    torch.bfloat16: (1e-2, 3e-2),
}
DEFAULT_TOL = TOLERANCES[torch.float32][0]


@dataclass
class Case:
    ref: Callable
    fast: Callable
    inputs: list
    params_ref: list = field(default_factory=list)
    params_fast: list = field(default_factory=list)
    grads: bool = True


@dataclass
class Pair:
    name: str
    build: Callable          # device -> Case
    tol: float = DEFAULT_TOL
    grad_tol: float | None = None    # None: TOLERANCES[dtype] gradient tolerance
    dtype: torch.dtype = torch.float32
    # Task 3: True = check() also requires two identical runs of the fast code to give identical bits.
    deterministic: bool = True

    @property
    def gtol(self) -> float:
        return self.grad_tol if self.grad_tol is not None else TOLERANCES[self.dtype][1]

    @property
    def drill(self) -> bool:
        return self.tol < DRILL_TOL and self.gtol < DRILL_TOL


def pair(name, tol=None, grad_tol=None, dtype=torch.float32, deterministic=True):
    assert dtype in TOLERANCES, f"{name}: no tolerances for {dtype}; measure them and add them to TOLERANCES"
    tol = TOLERANCES[dtype][0] if tol is None else tol
    grad_tol = TOLERANCES[dtype][1] if grad_tol is None else grad_tol
    if dtype == torch.float32:
        assert tol < DRILL_TOL and grad_tol < DRILL_TOL, f"{name}: fp32 tolerance must be < {DRILL_TOL}"

    def deco(fn):
        assert name not in PAIRS, f"duplicate pair {name}"
        PAIRS[name] = Pair(name, fn, tol, grad_tol, dtype, deterministic)
        return fn
    return deco


def pairs_in(module_name):
    """Names of the pairs a test module registered (for pytest.mark.parametrize)."""
    return [n for n, p in PAIRS.items() if p.build.__module__ == module_name]


def to64(module):
    """fp64 deep copy of a module, for references."""
    return copy.deepcopy(module).double()


def _check_output_structure(ref, fast, tol):
    """Check return structure and non-tensor metadata before tensor comparisons."""
    if isinstance(ref, torch.Tensor) or isinstance(fast, torch.Tensor):
        if not (isinstance(ref, torch.Tensor) and isinstance(fast, torch.Tensor)):
            raise AssertionError("output type mismatch")
    elif isinstance(ref, (tuple, list)) or isinstance(fast, (tuple, list)):
        if type(ref) is not type(fast) or len(ref) != len(fast):
            raise AssertionError("output structure mismatch")
        for ref_item, fast_item in zip(ref, fast):
            _check_output_structure(ref_item, fast_item, tol)
    elif type(ref) is not type(fast):
        raise AssertionError("non-tensor output type mismatch")
    elif isinstance(ref, float):
        if not (math.isfinite(ref) and math.isfinite(fast)
                and math.isclose(ref, fast, rel_tol=tol, abs_tol=tol)):
            raise AssertionError("non-tensor float output mismatch")
    elif ref != fast:
        raise AssertionError("non-tensor output mismatch")


def _as_tensor_list(obj: Any) -> list[torch.Tensor]:
    if isinstance(obj, torch.Tensor):
        return [obj]
    if isinstance(obj, (tuple, list)):
        tensors = []

        def collect(value):
            if isinstance(value, torch.Tensor):
                tensors.append(value)
            elif isinstance(value, (tuple, list)):
                for item in value:
                    collect(item)

        collect(obj)
        if not tensors:
            raise TypeError("output contained no tensors")
        return tensors
    raise TypeError(f"unsupported output type: {type(obj)}")


def _clone_inputs(inputs: list, *, dtype: torch.dtype, device) -> list:
    out: list = []
    for x in inputs:
        if isinstance(x, torch.Tensor):
            want = dtype if x.is_floating_point() else x.dtype
            y = x.detach().to(device=device, dtype=want).clone()
            if x.requires_grad and y.is_floating_point():
                y.requires_grad_(True)
            out.append(y)
        else:
            out.append(x)
    return out


def _zero_grads(tensors: list) -> None:
    for t in tensors:
        if isinstance(t, torch.Tensor) and t.grad is not None:
            t.grad = None


def rel_err(fast, ref) -> float:
    if not isinstance(fast, torch.Tensor) or not isinstance(ref, torch.Tensor):
        raise AssertionError(f"rel_err expects tensors, got {type(fast)} vs {type(ref)}")
    if fast.shape != ref.shape:
        raise AssertionError(
            f"shape mismatch: fast {tuple(fast.shape)} vs ref {tuple(ref.shape)}"
        )
    f = fast.detach().to(dtype=torch.float64)
    r = ref.detach().to(dtype=torch.float64)
    if not torch.isfinite(f).all() or not torch.isfinite(r).all():
        raise AssertionError("NaN/Inf in fast or ref")
    diff = f - r
    if not torch.isfinite(diff).all():
        raise AssertionError("NaN/Inf in difference")
    ref_norm = torch.linalg.vector_norm(r)
    diff_norm = torch.linalg.vector_norm(diff)
    if ref_norm.item() == 0.0:
        if diff_norm.item() == 0.0:
            return 0.0
        raise AssertionError("ref norm is zero but fast differs")
    err = (diff_norm / ref_norm).item()
    if not math.isfinite(err):
        raise AssertionError("NaN/Inf relative error")
    return float(err)


def scaled(k=1.01):
    """Return a factory: scaled(k)(fast_fn) multiplies every tensor output by k."""

    def decorate(fn):
        def wrapped(*args, **kwargs):
            out = fn(*args, **kwargs)
            if isinstance(out, torch.Tensor):
                return out * k
            if isinstance(out, tuple):
                return tuple(t * k if isinstance(t, torch.Tensor) else t for t in out)
            if isinstance(out, list):
                return [t * k if isinstance(t, torch.Tensor) else t for t in out]
            return out

        return wrapped

    return decorate


def _compare(p: Pair, name: str, fast, ref, tol: float, errors: dict) -> None:
    try:
        err = rel_err(fast, ref)
    except AssertionError as exc:
        raise AssertionError(f"{p.name}: {name}: {exc}") from exc
    if err > tol:
        raise AssertionError(f"{p.name}: {name}: rel_err={err:.6e} > tol={tol}")
    errors[name] = err


def _grad_or_zeros(t: torch.Tensor) -> torch.Tensor:
    return t.grad if t.grad is not None else torch.zeros_like(t)


def _check_determinism(p: Pair, case: Case, fast_fn, fast_inputs: list, fast_tensors: list, device) -> None:
    """Task 3: run the fast side a second time and require the same bits.

    Called by check() after the parity checks, when the first fast run has left its outputs in fast_tensors
    and its gradients in .grad of the fast inputs and params_fast. We keep copies of those, clear the
    gradients, run the fast code again on FRESH copies of the same inputs, push the SAME seeded cotangent
    back, and compare with torch.equal (exact, not a tolerance). Nothing here touches the reference.
    """
    first_out = [t.detach().clone() for t in fast_tensors]
    watched = [(f"grad_in[{i}]", t) for i, t in enumerate(fast_inputs)
               if isinstance(t, torch.Tensor) and t.requires_grad]
    watched += [(f"grad_param[{i}]", t) for i, t in enumerate(case.params_fast)]
    first_grad = {n: _grad_or_zeros(t).detach().clone() for n, t in watched} if case.grads else {}

    _zero_grads([t for _, t in watched])
    inputs2 = _clone_inputs(case.inputs, dtype=p.dtype, device=device)
    out2 = _as_tensor_list(fast_fn(*inputs2))

    def same(name, a, b):
        if not torch.equal(a, b.detach()):
            worst = (a.double() - b.detach().double()).abs().max().item()
            raise AssertionError(f"{p.name}: {name}: two identical runs of the fast code differ "
                                 f"(max abs diff {worst:.3e}): not deterministic. If that is by design "
                                 f"(CUDA atomics), register the pair with deterministic=False and say why.")

    if len(out2) != len(first_out):
        raise AssertionError(f"{p.name}: the second fast run returned {len(out2)} tensors, the first {len(first_out)}")
    for i, (a, b) in enumerate(zip(first_out, out2)):
        same(f"out[{i}]", a, b)
    if not case.grads:
        return

    diff = [t for t in out2 if t.requires_grad]
    gen = torch.Generator().manual_seed(0)           # the same cotangent as check() uses for the parity pass
    cot = [torch.randn(t.shape, dtype=torch.float64, generator=gen) for t in diff]
    torch.autograd.backward(diff, [g.to(t.device, t.dtype) for g, t in zip(cot, diff)])
    watched2 = [(f"grad_in[{i}]", t) for i, t in enumerate(inputs2)
                if isinstance(t, torch.Tensor) and t.requires_grad]
    watched2 += [(f"grad_param[{i}]", t) for i, t in enumerate(case.params_fast)]
    for (name, t) in watched2:
        same(name, first_grad[name], _grad_or_zeros(t))


def check(p: Pair, device, fast_override=None) -> dict:
    case = p.build(device)
    fast_fn = case.fast
    if fast_override is not None:
        fast_fn = fast_override(case.fast)

    ref_inputs = _clone_inputs(case.inputs, dtype=torch.float64, device=device)
    fast_inputs = _clone_inputs(case.inputs, dtype=p.dtype, device=device)

    ref_output = case.ref(*ref_inputs)
    fast_output = fast_fn(*fast_inputs)
    _check_output_structure(ref_output, fast_output, p.tol)
    ref_tensors = _as_tensor_list(ref_output)
    fast_tensors = _as_tensor_list(fast_output)
    if len(ref_tensors) != len(fast_tensors):
        raise AssertionError(
            f"{p.name}: output arity {len(fast_tensors)} vs {len(ref_tensors)}"
        )

    errors: dict[str, float] = {}
    for i, (ft, rt) in enumerate(zip(fast_tensors, ref_tensors)):
        _compare(p, f"out[{i}]", ft, rt, p.tol, errors)

    if case.grads:
        if len(case.params_ref) != len(case.params_fast):
            raise AssertionError(
                f"{p.name}: params arity {len(case.params_fast)} vs {len(case.params_ref)}"
            )
        _zero_grads(ref_inputs + fast_inputs + list(case.params_ref) + list(case.params_fast))

        diff = []
        for i, (rt, ft) in enumerate(zip(ref_tensors, fast_tensors)):
            if rt.requires_grad != ft.requires_grad:
                raise AssertionError(f"{p.name}: out[{i}]: requires_grad ref={rt.requires_grad} "
                                     f"fast={ft.requires_grad} (a detached output?)")
            if rt.requires_grad:
                diff.append((rt, ft))
        gen = torch.Generator().manual_seed(0)
        cot = [torch.randn(rt.shape, dtype=torch.float64, generator=gen) for rt, _ in diff]
        torch.autograd.backward([rt for rt, _ in diff], [g.to(rt.device, rt.dtype) for g, (rt, _) in zip(cot, diff)])
        torch.autograd.backward([ft for _, ft in diff], [g.to(ft.device, ft.dtype) for g, (_, ft) in zip(cot, diff)])

        named = [(f"grad_in[{i}]", ri, fi) for i, (ri, fi) in enumerate(zip(ref_inputs, fast_inputs))
                 if isinstance(ri, torch.Tensor) and ri.requires_grad]
        named += [(f"grad_param[{i}]", pr, pf) for i, (pr, pf) in enumerate(zip(case.params_ref, case.params_fast))]
        for name, r, f in named:
            if r.grad is None and f.grad is None:
                continue
            _compare(p, name, _grad_or_zeros(f), _grad_or_zeros(r), p.gtol, errors)

    # Task 3: the third check of the plan (parity above, determinism here, the 1.01 drill via fast_override).
    # Skipped when fast_override is set: the drill wants check() to fail on the parity step, and a wrapped
    # function would not be a fair test of the real fast code's determinism.
    if p.deterministic and fast_override is None:
        _check_determinism(p, case, fast_fn, fast_inputs, fast_tensors, device)

    if fast_override is None:
        outs = [v for k, v in errors.items() if k.startswith("out")]
        grads = [v for k, v in errors.items() if k.startswith("grad")]
        RESULTS[p.name] = {"dtype": str(p.dtype).replace("torch.", ""), "tol": p.tol, "grad_tol": p.gtol,
                           "out": max(outs), "grad": max(grads) if grads else None, "n": len(errors)}
    return errors
