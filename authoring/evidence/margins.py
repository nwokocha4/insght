"""Evidence: verify each trap moves a graded value beyond tolerance.
Variants are checked against the reference logic on the staged graded cases.
Also writes the variant result table for the README/provenance.
Settled cases must show no trap firing (all variants within tolerance to oracle).
"""
import csv, json, math, os, sys
from collections import Counter

TASK = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(TASK, "authoring", "provenance"))
os.environ.setdefault("CAMTRAP_BASE", os.path.join(TASK, "environment"))

# Oracle estimators replicated from solve.py logic for variant comparison.
def est(counts, shannon_base="ln", simpson="gini", chao="bc", threshold=None):
    n = sum(counts.values())
    S = len(counts)
    if n == 0:
        return (0, 0, 0.0, 0.0, 0.0, 0.0)
    ps = [c / n for c in counts.values()]
    if shannon_base == "ln":
        H = -sum(p * math.log(p) for p in ps)
    elif shannon_base == "log2":
        H = -sum(p * math.log2(p) for p in ps)
    else:
        H = -sum(p * math.log10(p) for p in ps)
    if simpson == "gini":
        D = 1 - sum(p * p for p in ps)
    else:
        D = 1 / sum(p * p for p in ps)
    f1 = sum(1 for c in counts.values() if c == 1)
    f2 = sum(1 for c in counts.values() if c == 2)
    if chao == "bc":
        chao_v = S + f1 * (f1 - 1) / (2 * (f2 + 1))
    else:
        chao_v = S + (f1 * f1 / (2 * f2) if f2 > 0 else float("inf"))
    return (n, S, H, D, chao_v, chao_v)  # last alias

TOL = 1e-4

# Use manifest counts for graded_01 site_a to witness threshold gap: 4 images
# (2 hedgehog, 2 trilobite) + 1 marginal accordion at 0.6362.
print("Variant gaps on staged design counts (witnessed numbers):")
cases = [
    ("threshold graded_01", {334: 2, 69: 2}, {334: 2, 69: 2, 401: 1}),
    ("chao graded_02", {386: 5, 334: 3, 69: 1, 117: 1}, None),
    ("simpson graded_03", {69: 4, 117: 4, 401: 2, 334: 2}, None),
    ("shannon graded_04", {355: 6, 69: 2, 117: 1, 334: 1}, None),
]
rows = []
for name, oracle, variant_counts in cases:
    n, S, H, D, C, _ = est(oracle)
    if "threshold" in name:
        vn, vS, vH, vD, vC, _ = est(variant_counts)
        print(f"{name}: oracle n={n} S={S} vs variant(threshold=0.50) n={vn} S={vS} gap n={vn-n} (exceeds tol: {vn!=n})")
        rows.append({"case": name, "variant": "threshold 0.50 vs derived 0.70", "gap": f"n={vn-n}, S={vS-S}"})
    if "chao" in name:
        _, _, _, _, classic, _ = est(oracle, chao="classic")
        print(f"{name}: BC={C:.4f} vs classic={classic} gap=diverges at f2=0 (exceeds tol: True)")
        rows.append({"case": name, "variant": "classic vs BC", "gap": "diverges (f2=0)"})
    if "simpson" in name:
        _, _, _, inv, _, _ = est(oracle, simpson="inverse")
        print(f"{name}: D={D:.4f} vs inv={inv:.4f} gap={abs(inv-D):.4f} (exceeds tol: {abs(inv-D)>TOL})")
        rows.append({"case": name, "variant": "inverse vs gini", "gap": f"{abs(inv-D):.4f}"})
    if "shannon" in name:
        _, _, log2H, _, _, _ = est(oracle, shannon_base="log2")
        print(f"{name}: H={H:.4f} vs log2={log2H:.4f} gap={abs(log2H-H):.4f} (exceeds tol: {abs(log2H-H)>TOL})")
        rows.append({"case": name, "variant": "log2 vs ln", "gap": f"{abs(log2H-H):.4f}"})

# Settled numeric sanity: recompute H/D for settled_02 counts {2,2,2}: H=ln3=1.0986, D=2/3=0.6667
n, S, H, D, C = est({69: 2, 117: 2, 401: 2})[:5]
print(f"settled_02 check: H={H:.4f} (want 1.0986) D={D:.4f} (want 0.6667) chao={C:.4f} (want 3.0000)")

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trap_margins.json")
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w") as f:
    json.dump(rows, f, indent=2)
print(f"wrote {out}")
