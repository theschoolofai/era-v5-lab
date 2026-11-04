"""Locate the upstream ``kronecker_embeddings`` package (theschoolofai/kronecker-embeddings).

The normal route is ``pip install`` (see ``src/requirements.txt``). For a source checkout, entry
points call :func:`ensure_kronecker_embeddings`, which also tries ``$KRONECKER_SRC`` and a sibling
``kronecker-embeddings/src`` folder next to the lab repository. Library modules never edit
``sys.path`` themselves.
"""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

from .config import TEAM_DIR

_HINT = (
    "kronecker_embeddings not found. pip install -r teams/04-ke2/src/requirements.txt, or clone "
    "https://github.com/theschoolofai/kronecker-embeddings and set KRONECKER_SRC to its src folder."
)


def ensure_kronecker_embeddings() -> Path:
    """Make ``kronecker_embeddings`` importable and return the folder that contains it."""
    try:
        module = importlib.import_module("kronecker_embeddings")
    except ImportError:
        candidates = [os.environ.get("KRONECKER_SRC"), TEAM_DIR.parents[2] / "kronecker-embeddings" / "src"]
        for c in candidates:
            if c and (Path(c) / "kronecker_embeddings").is_dir():
                sys.path.insert(0, str(c))
                module = importlib.import_module("kronecker_embeddings")
                break
        else:
            raise ImportError(_HINT) from None
    return Path(module.__file__).resolve().parents[1]
