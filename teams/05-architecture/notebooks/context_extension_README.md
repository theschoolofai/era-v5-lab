# Context-extension pilot

Open [context_extension.ipynb](context_extension.ipynb) in Jupyter, VS Code or Colab.
The notebook contains the WikiText pilot code and clearly labelled recorded
results with embedded charts. Code cells have no execution counts: this format
conversion has been checked locally but has not been freshly executed on a GPU.

The primary G5-corpus result uses eager attention and the full vocabulary head.
It remains in [the separate runner](../harness/context_extension_check.py) and
[the submission plan](../docs/long_context_plan.md). The notebook uses SDPA and a
tail-only head for exploratory evaluation; its results are not pooled with G5.

## Run

Use Python 3.13 and a CUDA GPU supporting BF16 with a compatible driver.
From the repository root:

```bash
python -m pip install -r teams/05-architecture/notebooks/requirements-context-extension.txt
jupyter lab teams/05-architecture/notebooks/context_extension.ipynb
```

Select the matching Python kernel and Run All. Public model and dataset
revisions are pinned in the notebook. New outputs are written to
`out/context_extension_pilot/` beneath the kernel working directory; committed
measurements are not overwritten. Keep generated outputs outside the public
team folders. Full GPU execution includes a batch sweep up to 48 inputs.

For a noninteractive run, write the executed notebook outside the source tree:

```bash
jupyter nbconvert --to notebook --execute --ExecutePreprocessor.timeout=1800 --output context_extension_executed.ipynb --output-dir /tmp teams/05-architecture/notebooks/context_extension.ipynb
```

The offline evidence check needs only Python's standard library:

```bash
python teams/05-architecture/tests/verify_context_extension.py
```

Original executed source and replay hashes remain in
[source_provenance.json](../results/context_extension/source_provenance.json).
The historical source is preserved in Git commit
`9539c7be6263b3fe429a5096dac8c77ed1428f63`.
