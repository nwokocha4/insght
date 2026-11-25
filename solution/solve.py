"""Camtrap per-site diversity estimation from resnet18 species detections.

Reads every case directory directly under <base>/data (excluding `reference`),
runs each frame in <case>/images/<site_id>/*.jpg through resnet18.a1_in1k
with preprocessing exactly from timm resolve_data_config, counts only
vocabulary top-1 detections with confidence >= 0.65, aggregates per site,
and writes one estimate table per case to <base>/output/<case>_estimate.csv.

Base defaults to /app; override with CAMTRAP_BASE for local testing.
Method authority: environment/data/reference/camtrap_diversity_method.pdf.

Deterministic: single pass, no test-time augmentation, model in eval mode,
torch.no_grad, every image decoded and preprocessed identically.
"""

import csv
import math
import os
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP

import torch
import timm
from timm.data import create_transform, resolve_data_config
from PIL import Image

BASE = os.environ.get("CAMTRAP_BASE", "/app")
MODEL_NAME = "resnet18.a1_in1k"
VOCAB = {386, 69, 117, 401, 355, 334}
CONF_THRESHOLD = 0.65


def q4(x):
    return Decimal(str(x)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def read_site_ids(case_dir):
    path = os.path.join(case_dir, "sites.csv")
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    return sorted({(r.get("site_id") or "").strip() for r in rows} - {""})


def load_model():
    model = timm.create_model(MODEL_NAME, pretrained=True)
    model.eval()
    config = resolve_data_config({}, model=model)
    transform = create_transform(**config, is_training=False)
    return model, transform


def site_image_paths(case_dir, site_id):
    folder = os.path.join(case_dir, "images", site_id)
    if not os.path.isdir(folder):
        return []
    return sorted(
        os.path.join(folder, name)
        for name in os.listdir(folder)
        if name.lower().endswith(".jpg")
        and os.path.isfile(os.path.join(folder, name))
    )


def classify_images(model, transform, paths):
    """Yield (top1_index, top1_confidence) for each image path."""
    for path in paths:
        with Image.open(path) as img:
            tensor = transform(img.convert("RGB")).unsqueeze(0)
        with torch.no_grad():
            probs = torch.softmax(model(tensor), dim=1)[0]
        top1 = int(torch.argmax(probs).item())
        conf = float(probs[top1].item())
        yield top1, conf


def diversity_row(site_id, counts):
    n = sum(counts.values())
    S = len(counts)
    if n == 0:
        return {
            "site_id": site_id,
            "n_det": "0",
            "S": "0",
            "H": "0.0000",
            "D": "0.0000",
            "chao": "0.0000",
        }
    H = 0.0
    D = 0.0
    f1 = 0
    f2 = 0
    for c in counts.values():
        p = c / n
        H -= p * math.log(p)
        if c == 1:
            f1 += 1
        elif c == 2:
            f2 += 1
    D = 1.0 - sum((c / n) ** 2 for c in counts.values())
    chao = S + f1 * (f1 - 1) / (2 * (f2 + 1))
    return {
        "site_id": site_id,
        "n_det": str(n),
        "S": str(S),
        "H": format(q4(H), ".4f"),
        "D": format(q4(D), ".4f"),
        "chao": format(q4(chao), ".4f"),
    }


def solve_case(case_dir, model, transform):
    rows = []
    for site_id in read_site_ids(case_dir):
        paths = site_image_paths(case_dir, site_id)
        counts = Counter()
        for top1, conf in classify_images(model, transform, paths):
            if top1 not in VOCAB:
                continue
            if conf < CONF_THRESHOLD:
                continue
            counts[top1] += 1
        rows.append(diversity_row(site_id, counts))
    rows.sort(key=lambda r: r["site_id"])
    return rows


def main():
    data = os.path.join(BASE, "data")
    outdir = os.path.join(BASE, "output")
    os.makedirs(outdir, exist_ok=True)
    cases = sorted(
        d
        for d in os.listdir(data)
        if os.path.isdir(os.path.join(data, d)) and d != "reference"
    )
    if not cases:
        print("no cases under %s" % data)
        return
    model, transform = load_model()
    for case in cases:
        rows = solve_case(os.path.join(data, case), model, transform)
        with open(
            os.path.join(outdir, "%s_estimate.csv" % case),
            "w",
            newline="",
            encoding="utf-8",
        ) as f:
            w = csv.DictWriter(
                f, fieldnames=["site_id", "n_det", "S", "H", "D", "chao"]
            )
            w.writeheader()
            w.writerows(rows)
        print("wrote %s (%d rows)" % (case, len(rows)))


if __name__ == "__main__":
    main()
