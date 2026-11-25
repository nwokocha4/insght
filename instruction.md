# Camera-Trap Per-Site Diversity Estimation

Estimate per-site species diversity from camera-trap images with a fixed pretrained classifier. Method authority: `/app/data/reference/camtrap_diversity_method.pdf`. This brief states case, file, detection and output mechanics.

Cases in `/app/data` (`reference/` excluded). Each case has `sites.csv` (roster) and `images/<site_id>/*.jpg`. Read `sites.csv` for `site_id` values; each roster site gets one output row.

Model: `resnet18.a1_in1k` via `timm`, `pretrained=True`, eval mode, `torch.no_grad`. Preprocessing is exactly `timm.data.resolve_data_config` plus `create_transform(..., is_training=False)` — resize 224x224 bicubic, normalize RGB mean `(0.485, 0.456, 0.406)` std `(0.229, 0.224, 0.225)`, center crop scaled by 0.95. No augmentation. Decode each image with PIL `.convert("RGB")`.

Vocabulary is exactly these six ImageNet top-1 indices: `386` elephant, `69` trilobite, `117` nautilus, `401` accordion, `355` llama, `334` hedgehog. A frame counts only if top-1 is in this set AND softmax confidence `>= 0.65` (inclusive). Otherwise it adds nothing. Blank/vegetation frames have no separate detector; they fail this threshold.

Per site let `n` be counted detections, `S` distinct vocab species, `count_i` per species, `p_i = count_i / n`. Formulas (normative):
- Shannon `H = -sum(p_i * ln(p_i))` with natural log.
- Simpson `D = 1 - sum(p_i^2)` (Gini-Simpson, not the inverse form).
- Chao bias-corrected `chao = S + f1*(f1-1) / (2*(f2+1))` where `f1` = #species with count 1, `f2` = #species with count 2. (Classic `S + f1^2/(2*f2)` is wrong here.)

Degenerate: if `n = 0` report `S=0, H=0, D=0, chao=0`. Round `H`, `D`, `chao` half up to 4dp; `n`, `S` integers.

Run `python3 /app/solve.py`; write `/app/output/<case>_estimate.csv` with header `site_id,n_det,S,H,D,chao`; key `site_id`, row order free. Missing/duplicate/unknown/nonnumeric rows fail. `H`, `D`, `chao` tolerance `0.0001`; `n_det`, `S` exact.

You have 28800 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
