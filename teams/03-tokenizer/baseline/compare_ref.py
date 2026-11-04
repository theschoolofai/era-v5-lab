import json

ref  = json.load(open("reference_outputs/evaluate_fertility_flores.json", encoding="utf-8"))
mine = json.load(open("evaluate_fertility_flores.json", encoding="utf-8"))

def walk(a, b, path=""):
    if isinstance(a, dict):
        for k in a:
            if k in b:
                yield from walk(a[k], b[k], f"{path}/{k}")
            else:
                print("missing in mine:", f"{path}/{k}")
    elif isinstance(a, list):
        for i, (x, y) in enumerate(zip(a, b)):
            yield from walk(x, y, f"{path}[{i}]")
    elif isinstance(a, (int, float)) and not isinstance(a, bool) and isinstance(b, (int, float)):
        yield path, a, b, abs(a - b)

worst = 0
for path, r, m, d in walk(ref, mine):
    if "Brahmic" not in path or "time" in path.lower() or "sec" in path.lower():
        continue
    flag = "  <-- DIFF > 0.001" if d > 0.001 else ""
    print(f"{path:60s} ref={r:<12} mine={m:<12} diff={d:.6f}{flag}")
    worst = max(worst, d)

print("\nLargest difference:", worst)
print("RESULT:", "PASS (within 0.001)" if worst <= 0.001 else "CHECK THE FLAGGED ROWS")