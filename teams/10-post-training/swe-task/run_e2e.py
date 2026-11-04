"""End-to-end SWE task runner inside Docker.

1. Seeds buggy `calc.py` (`return a + b + 1`).
2. Runs `python -m unittest test_calc.py` -> captures failing output (exit 1).
3. Applies the patch (`return a + b`).
4. Re-runs `python -m unittest test_calc.py` -> captures passing output (exit 0).
5. Renders and parses the complete multi-turn trajectory with `render.py` (`effort="4k"`).
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

WORK = Path(__file__).resolve().parent
CALC = WORK / "calc.py"
_RENDER_CANDIDATES = (
    WORK / "render.py",
    WORK.parent / "chat-format" / "render.py",
)
_RENDER_PATH = next(p for p in _RENDER_CANDIDATES if p.exists())
_spec = importlib.util.spec_from_file_location("g10_render", _RENDER_PATH)
assert _spec is not None and _spec.loader is not None
render_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(render_mod)


def run_tests() -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "test_calc.py"],
        cwd=WORK,
        capture_output=True,
        text=True,
    )
    output = (proc.stdout + proc.stderr).strip()
    return proc.returncode, output


def main() -> int:
    # 1. Seed the buggy version and verify test failure.
    CALC.write_text("def add(a, b):\n    return a + b + 1\n", encoding="utf-8")
    before_src = CALC.read_text(encoding="utf-8")
    fail_code, fail_out = run_tests()
    print(f"[step 1] initial test exit={fail_code}")
    print(fail_out)
    assert fail_code != 0, "expected initial buggy version to fail"

    # 2. Apply the fix and verify test pass.
    patched_src = before_src.replace("return a + b + 1", "return a + b")
    CALC.write_text(patched_src, encoding="utf-8")
    pass_code, pass_out = run_tests()
    print(f"[step 2] post-patch test exit={pass_code}")
    print(pass_out)
    assert pass_code == 0, "expected patched version to pass"

    # 3. Render and round-trip parse the agent trajectory in chat_format_v0.
    messages = [
        {
            "role": "system",
            "content": "You edit code and you report only what a tool returned.",
        },
        {"role": "user", "content": "test_add fails in calc.py. Fix add."},
        {
            "role": "assistant",
            "content": "I am reading calc.py before editing it.",
            "tool_calls": [
                {"name": "read_file", "arguments": {"path": "calc.py"}},
            ],
        },
        {"role": "tool", "content": before_src},
        {
            "role": "assistant",
            "content": "Removed the extra increment.",
            "tool_calls": [
                {
                    "name": "apply_patch",
                    "arguments": {"path": "calc.py", "patch": "return a + b"},
                }
            ],
        },
        {"role": "tool", "content": pass_out},
        {
            "role": "assistant",
            "content": "test_calc.py passes with exit code 0.",
        },
    ]
    transcript = render_mod.render(messages, effort="4k")
    parsed = render_mod.parse(transcript)
    assert parsed["effort"] == "4k"
    assert len(parsed["messages"]) == len(messages)
    print(
        f"[step 3] chat_format_v0 render/parse verified: effort={parsed['effort']} turns={len(parsed['messages'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
