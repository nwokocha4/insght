"""Seeded generator: stages Caltech-101 subsets into case directories.

Model-aware: every candidate image is scored with the exact reference
preprocessing before being placed, so graded cases hit their design
counts deterministically. Output cases are verified against the
reference estimators to guarantee trap gaps exceed tolerance.

Caltech source: scratch_camtrap/caltech101/101_ObjectCategories
Blanks: procedurally generated vegetation/soil frames (deterministic RNG
from seed below), matching probe_blank.py generation.

Run: .venv/Scripts/python.exe authoring/provenance/seeded_generator.py
Writes: environment/data/<case>/ (settled_01, settled_02, graded_01..06)
Also writes manifest beside each case for provenance.
"""
import csv, json, os, random, shutil, sys
from collections import Counter

ROOT = os.path.dirname(os.path.abspath(__file__))  # authoring/provenance: seeded_generator.py lives here
TASK = os.path.abspath(os.path.join(ROOT, "..", ".."))
ENV_DATA = os.path.join(TASK, "environment", "data")
CALTECH = r"C:\Users\Hopewell\Desktop\reed\scratch_camtrap\caltech101\101_ObjectCategories"
MANIFEST_DIR = os.path.join(TASK, "authoring", "provenance", "manifests")

SEED = 20261111
VOCAB = {386: "elephant", 69: "trilobite", 117: "nautilus", 401: "accordion",
         355: "llama", 334: "hedgehog"}
# Caltech folder -> vocab index for animals (used only to find candidates;
# final acceptance is always measured top1/conf, never folder label).
CLASS_FOLDERS = {
    386: ["elephant"],
    69: ["trilobite"],
    117: ["nautilus"],
    401: ["accordion"],
    355: ["llama"],
    334: ["hedgehog"],
}
# Extra folders mined for threshold-window images (top1 lands in vocab but conf near 0.65).
MINING_FOLDERS = ["elephant", "butterfly", "llama", "kangaroo", "platypus",
                  "hedgehog", "trilobite", "nautilus", "accordion"]


def load_model():
    import torch, timm
    from timm.data import create_transform, resolve_data_config
    model = timm.create_model("resnet18.a1_in1k", pretrained=True)
    model.eval()
    cfg = resolve_data_config({}, model=model)
    tf = create_transform(**cfg, is_training=False)
    return model, tf


def score_images(model, tf, paths):
    import torch
    from PIL import Image
    out = {}
    for p in paths:
        with Image.open(p) as im:
            x = tf(im.convert("RGB")).unsqueeze(0)
            with torch.no_grad():
                probs = torch.softmax(model(x), dim=1)[0]
                top1 = int(torch.argmax(probs).item())
                conf = float(probs[top1].item())
        out[p] = (top1, conf)
    return out


def make_blank(path, rng, kind):
    """Deterministic synthetic blank: vegetation/soil/grey/uniform."""
    from PIL import Image
    import numpy as np
    w, h = 800, 600
    if kind == "vegetation":
        base = np.array([60, 90, 45], dtype=float)
        noise = np.random.default_rng(rng.randrange(1 << 30)).normal(0, 18, (h, w, 3))
    elif kind == "soil":
        base = np.array([110, 88, 62], dtype=float)
        noise = np.random.default_rng(rng.randrange(1 << 30)).normal(0, 22, (h, w, 3))
    elif kind == "grey":
        base = np.array([128, 128, 128], dtype=float)
        noise = np.random.default_rng(rng.randrange(1 << 30)).normal(0, 6, (h, w, 3))
    else:  # uniform green
        base = np.array([45, 110, 55], dtype=float)
        noise = np.random.default_rng(rng.randrange(1 << 30)).normal(0, 4, (h, w, 3))
    img = np.clip(base + noise, 0, 255).astype("uint8")
    Image.fromarray(img).save(path, "JPEG", quality=88)


def stage_case(case, sites, plan, pool, blanks_per_site, rng, manifest):
    """plan: {site_id: [(top1, conf_check_fn, n_images), ...]} simplified:
    plan is list of (site_id, picks) where picks is list of (idx, conf, path, want)."""
    case_dir = os.path.join(ENV_DATA, case)
    if os.path.isdir(case_dir):
        shutil.rmtree(case_dir)
    os.makedirs(case_dir)
    with open(os.path.join(case_dir, "sites.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["site_id"])
        for s in sites:
            w.writerow([s])
    manifest_rows = []
    for site_id, items in plan:
        dest = os.path.join(case_dir, "images", site_id)
        os.makedirs(dest, exist_ok=True)
        for i, (src_path, top1, conf) in enumerate(items):
            dest_path = os.path.join(dest, f"frame_{i+1:04d}.jpg")
            shutil.copyfile(src_path, dest_path)
            manifest_rows.append({"case": case, "site_id": site_id,
                                  "file": dest_path, "src": src_path,
                                  "top1": top1, "conf": round(conf, 4), "kind": "animal"})
        for j in range(blanks_per_site.get(site_id, 0)):
            kind = ["vegetation", "soil", "grey", "uniform"][j % 4]
            dest_path = os.path.join(dest, f"blank_{j+1:02d}.jpg")
            make_blank(dest_path, rng, kind)
            manifest_rows.append({"case": case, "site_id": site_id, "file": dest_path,
                                  "src": f"synthetic:{kind}", "top1": None, "conf": None, "kind": "blank"})
    manifest.append(manifest_rows)


def pick(pool, top1_target, n, conf_min=0.75, conf_max=1.0, exclude_ids=None):
    """Greedy pick n images with given top1 and conf in window."""
    exclude = exclude_ids or set()
    out = []
    for p, (t1, conf) in sorted(pool.items()):
        if len(out) >= n:
            break
        if id(p) in exclude:
            continue
        if t1 == top1_target and conf_min <= conf <= conf_max:
            out.append((p, t1, conf))
    return out


def main():
    import glob
    rng = random.Random(SEED)
    model, tf = load_model()
    paths = []
    for folder in set(MINING_FOLDERS):
        paths += sorted(glob.glob(os.path.join(CALTECH, folder, "*.jpg")))
    rng.shuffle(paths)
    print(f"scoring {len(paths)} candidate images...")
    pool = score_images(model, tf, paths)
    print(f"scored. Sample pools:")
    by_top1 = Counter(t for t, c in pool.values() if c >= 0.65 and t in VOCAB)
    print(dict(by_top1))
    used = set()

    def take(top1, n, lo=0.75, hi=1.0):
        nonlocal used
        got = []
        for p, (t1, c) in sorted(pool.items()):
            if len(got) >= n:
                break
            if p in used:
                continue
            if t1 == top1 and lo <= c <= hi:
                got.append((p, t1, c))
                used.add(p)
        return got

    manifest = []
    # settled_01: two sites, each f1=0, no trap firing
    s1a = take(386, 2) + take(69, 2) + take(117, 2) + take(334, 1)
    s1b = take(401, 2) + take(355, 1) + take(334, 2) + take(69, 1)
    stage_case("settled_01", ["site_a", "site_b"],
               [("site_a", s1a), ("site_b", s1b)],
               pool, {"site_a": 2, "site_b": 2}, rng, manifest)
    # settled_02: single site, even mix
    s2a = take(69, 2) + take(117, 2) + take(401, 2)
    stage_case("settled_02", ["site_a"], [("site_a", s2a)],
               pool, {"site_a": 1}, rng, manifest)
    # graded_01 threshold: one marginal image conf 0.55-0.64 in-vocab at site_a
    marginal = None
    for p, (t1, c) in sorted(pool.items()):
        if p not in used and t1 in VOCAB and 0.55 <= c <= 0.64:
            marginal = (p, t1, c)
            used.add(p)
            break
    assert marginal, "no marginal in-vocab image found for threshold case"
    g1a = take(334, 2) + take(69, 2) + [marginal]
    g1b = take(117, 3) + take(401, 2)
    stage_case("graded_01", ["site_a", "site_b"],
               [("site_a", g1a), ("site_b", g1b)],
               pool, {"site_a": 1, "site_b": 1}, rng, manifest)
    print(f"graded_01 marginal: top1={marginal[1]} conf={marginal[2]:.4f} src={marginal[0]}")
    # graded_02 Chao: f1=2, f2=0 -> classic diverges, BC finite
    g2a = take(386, 5) + take(334, 3) + take(69, 1) + take(117, 1)
    stage_case("graded_02", ["site_a"], [("site_a", g2a)], pool, {}, rng, manifest)
    # graded_03 Simpson: counts 4,4,2,2 -> D vs inverse gap > 1
    g3a = take(69, 4) + take(117, 4) + take(401, 2) + take(334, 2)
    stage_case("graded_03", ["site_a"], [("site_a", g3a)], pool, {}, rng, manifest)
    # graded_04 Shannon: counts 6,2,1,1 -> ln vs log10/log2 gap
    g4a = take(355, 6) + take(69, 2) + take(117, 1) + take(334, 1)
    stage_case("graded_04", ["site_a"], [("site_a", g4a)], pool, {}, rng, manifest)
    # graded_05 blanks: 3 blanks + 4 animals
    g5a = take(69, 2) + take(334, 2)
    stage_case("graded_05", ["site_a"], [("site_a", g5a)], pool, {"site_a": 3}, rng, manifest)
    # graded_06 edge: empty site (blanks only) + single-detection site
    g6b = take(117, 1)
    stage_case("graded_06", ["site_empty", "site_single"],
               [("site_empty", []), ("site_single", g6b)],
               pool, {"site_empty": 2}, rng, manifest)

    os.makedirs(MANIFEST_DIR, exist_ok=True)
    with open(os.path.join(MANIFEST_DIR, "camtrap_manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"staged 8 cases under {ENV_DATA}")
    print("Run reference solve.py (CAMTRAP_BASE=environment) to produce expected rows.")


if __name__ == "__main__":
    main()
