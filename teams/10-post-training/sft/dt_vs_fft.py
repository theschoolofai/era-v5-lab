"""Equal-step comparison of Deletion Tuning, LoRA, and full fine-tuning.

The local run uses one synthetic slice so the update rules can be checked
without a GPU. The open-model run is the job request. This script does not
download a model and does not read benchmark items.

    python teams/10-post-training/sft/dt_vs_fft.py --steps 30 --seed 0
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _dt():
    spec = importlib.util.spec_from_file_location("g10_deletion_tuning", HERE / "deletion_tuning.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


DT = _dt()


def _copy(weight):
    return [row[:] for row in weight]


def _flatten(weight):
    return [value for row in weight for value in row]


def _unflatten(values, rows, cols):
    return [values[row * cols:(row + 1) * cols] for row in range(rows)]


def _forward(weight, inputs):
    preds = []
    for sample in inputs:
        preds.append([math.tanh(sum(value * feature for value, feature in zip(row, sample))) for row in weight])
    return preds


def _task_loss(weight, inputs, targets):
    preds = _forward(weight, inputs)
    total = 0.0
    count = 0
    for pred, target in zip(preds, targets):
        for left, right in zip(pred, target):
            total += (left - right) * (left - right)
            count += 1
    return total / count


def _column_norms(inputs, cols):
    norms = []
    for col in range(cols):
        norms.append(math.sqrt(sum(sample[col] * sample[col] for sample in inputs)))
    return norms


def _synthetic_slice(rng, rows, cols, samples):
    base = [[rng.uniform(-0.3, 0.3) for _ in range(cols)] for _ in range(rows)]
    teacher = [[value + rng.uniform(-0.2, 0.2) for value in row] for row in base]
    inputs = [[rng.uniform(-1.0, 1.0) for _ in range(cols)] for _ in range(samples)]
    targets = _forward(teacher, inputs)
    return base, inputs, targets


def _effective(method, base, state, step, total_steps):
    rows = len(base)
    cols = len(base[0])
    if method == "fft":
        return state["weight"]
    if method == "lora":
        return [
            [base[row][col] + state["b"][row] * state["a"][col] for col in range(cols)]
            for row in range(rows)
        ]
    alpha = DT.sharpness(step, total_steps)
    masked = DT.apply_mask(base, DT.soft_mask(state["logits"], alpha))
    return masked


def _pack_grad(method, grad_weight, state):
    rows = len(grad_weight)
    cols = len(grad_weight[0])
    if method == "fft":
        return _flatten(grad_weight)
    if method == "lora":
        grad_a = [0.0] * cols
        grad_b = [0.0] * rows
        for row in range(rows):
            for col in range(cols):
                grad_a[col] += grad_weight[row][col] * state["b"][row]
                grad_b[row] += grad_weight[row][col] * state["a"][col]
        return grad_a + grad_b
    alpha = state["alpha"]
    mask = DT.soft_mask(state["logits"], alpha)
    flat_base = _flatten(state["base"])
    flat_grad = _flatten(grad_weight)
    grad_logits = []
    for base_value, grad_value, bit in zip(flat_base, flat_grad, mask):
        grad_logits.append(grad_value * base_value * alpha * bit * (1.0 - bit))
    return grad_logits


def _task_grad(weight, inputs, targets):
    rows = len(weight)
    cols = len(weight[0])
    grad = [[0.0] * cols for _ in range(rows)]
    preds = _forward(weight, inputs)
    scale = 2.0 / (len(inputs) * rows)
    for sample, pred, target in zip(inputs, preds, targets):
        for row in range(rows):
            residual = pred[row] - target[row]
            slope = 1.0 - pred[row] * pred[row]
            for col in range(cols):
                grad[row][col] += scale * residual * slope * sample[col]
    return grad


def _params(method, state):
    if method == "fft":
        return _flatten(state["weight"])
    if method == "lora":
        return state["a"] + state["b"]
    return state["logits"]


def _set_params(method, state, values):
    rows = len(state["base"])
    cols = len(state["base"][0])
    if method == "fft":
        state["weight"] = _unflatten(values, rows, cols)
    elif method == "lora":
        state["a"] = values[:cols]
        state["b"] = values[cols:]
    else:
        state["logits"] = values


def compare(steps: int = 30, seed: int = 0, rows: int = 4, cols: int = 4, samples: int = 32, lr: float = 0.2) -> dict:
    """Run the three methods for the same number of steps on one synthetic slice."""
    if steps <= 0:
        raise ValueError("steps must be positive")
    rng = random.Random(seed)
    base, inputs, targets = _synthetic_slice(rng, rows, cols, samples)
    scores = DT.wanda_scores(base, _column_norms(inputs, cols))
    logit_rng = random.Random(seed + 1)
    methods = {}
    for method in ("dt", "lora", "fft"):
        state = {"base": _copy(base)}
        if method == "fft":
            state["weight"] = _copy(base)
        elif method == "lora":
            lora_rng = random.Random(seed + 2)
            state["a"] = [lora_rng.gauss(0.0, 0.02) for _ in range(cols)]
            state["b"] = [0.0] * rows
        else:
            state["logits"] = DT.init_logits(scores, logit_rng)
        start_weight = _effective(method, base, state, 0, steps)
        loss_start = _task_loss(start_weight, inputs, targets)
        if method == "dt":
            loss_start = DT.deletion_loss(loss_start, start_weight)
        for step in range(steps):
            state["alpha"] = DT.sharpness(step, steps)
            current = _effective(method, base, state, step, steps)
            grad = _task_grad(current, inputs, targets)
            if method == "dt":
                # d/dG of -lambda * ||W * mask||^2, through the soft mask.
                alpha = state["alpha"]
                mask = DT.soft_mask(state["logits"], alpha)
                flat = _flatten(current)
                cursor = 0
                for row in range(rows):
                    for col in range(cols):
                        bit = mask[cursor]
                        extra = -2.0 * DT.LAMBDA_SFT * flat[cursor] * base[row][col] * alpha * bit * (1.0 - bit)
                        grad[row][col] += extra
                        cursor += 1
            packed = _pack_grad(method, grad, state)
            values = _params(method, state)
            _set_params(method, state, [value - lr * part for value, part in zip(values, packed)])
        end_weight = _effective(method, base, state, steps, steps)
        loss_end = _task_loss(end_weight, inputs, targets)
        if method == "dt":
            loss_end = DT.deletion_loss(loss_end, end_weight)
            keep = DT.hard_keep(state["logits"])
            deleted = keep.count(False) / len(keep)
        else:
            deleted = None
        methods[method] = {
            "steps": steps,
            "loss_start": loss_start,
            "loss_end": loss_end,
            "base_unchanged": state.get("weight", base) == base if method != "fft" else state["weight"] != base,
            "deleted_fraction": deleted,
        }
        if method == "fft":
            methods[method]["base_unchanged"] = False
            methods[method]["base_changed"] = state["weight"] != base
        else:
            methods[method]["base_changed"] = False
    return {"seed": seed, "steps": steps, "slice": "synthetic", "rows": samples, "methods": methods}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, default=30)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    print(json.dumps(compare(steps=args.steps, seed=args.seed), indent=2))


if __name__ == "__main__":
    main()
