# Camera-Trap Diversity Estimation

Taxonomy: TB-Science domain `Science`, field `Ecology`; repository track `science-ecology` (camera-trap biodiversity monitoring).

Ecologist brief. The agent runs a fixed pretrained classifier over camera-trap frames, counts only vocabulary detections above confidence, and reports per-site Shannon, Simpson and bias-corrected Chao estimates. The governing text is the method note in `environment/data/reference/camtrap_diversity_method.pdf`; the instruction brief states the office practice that controls where the note is silent.

## Difficulty

Four witnessed traps, each moving a graded value well beyond the `0.0001` tolerance. Measured on the staged graded cases (`authoring/evidence/trap_margins.json`):

1. **Confidence threshold** (`>= 0.65` inclusive). `graded_01` holds an accordion frame at confidence `0.6362` on the site roster. Dropping the bound to `0.50` counts it and moves the site from `n=4, S=2` to `n=5, S=3`, which shifts `H`, `D` and `chao` as well. Counting frames below the bound shifts graded values far beyond tolerance.
2. **Chao bias-corrected vs classic**. `graded_02` has `f1=2, f2=0`, so the bias-corrected form gives `chao = 5.0000` while the classic `S + f1^2/(2*f2)` divides by zero and diverges. The method note's own worked check carries the same `f1=2, f2=0` shape.
3. **Simpson form**. `graded_03` (counts `4,4,2,2`) gives Gini-Simpson `D = 0.7222`; the inverse form `1/sum(p^2)` gives `3.6000`, a gap of `2.8778`.
4. **Shannon base**. `graded_04` (counts `6,2,1,1`) gives natural-log `H = 1.0889`; base 2 gives `1.5710`, a gap of `0.4821`.

`graded_05` carries three synthetic blank frames beside four detections, and `graded_06` carries an empty site beside a single-detection site, so a program that counts blanks or mishandles `n=0` fails visibly.

Preprocessing (resize 224 bicubic, ImageNet normalization, `0.95` center crop via `timm` data config) and blank handling (exclusion via the `0.65` threshold, no separate detector) are **specification, not traps**: they are stated normatively in the brief and method note so the agent can reproduce detections exactly. Measured blanks score `0.01` to `0.21` top-1 confidence, far under the bound, and preprocessing variants do not flip a staged top-1, so claiming either as a graded trap would be unfair.

## Reference solution

`solution/solve.py` loads `resnet18.a1_in1k` via `timm`, preprocesses each `images/<site_id>/*.jpg` via `resolve_data_config`/`create_transform(is_training=False)`, counts only top-1 in `{386, 69, 117, 401, 355, 334}` with confidence `>= 0.65`, aggregates per site, and writes one estimate table per case with natural-log Shannon, Gini-Simpson, and bias-corrected Chao, rounded half up to 4dp. `solution/solve.sh` stages the reference into place and smoke runs it on the settled cases. `authoring/provenance/reference_build/build_reference.py` regenerates the method PDF from the embedded pages.

## Verification

`tests/test_outputs.py` stages each graded case fresh under `/app`, runs the submitted `/app/solve.py` with a time limit, and keys every output row by `site_id` with order free. Missing rows, duplicated keys, unknown keys, and nonnumeric `H`/`D`/`chao` values fail the case. `H`, `D`, `chao` must each match within `0.0001`; `n_det` and `S` must match exactly. `tests/expected.json` holds the oracle rows. `tests/test.sh` runs the suite, emits CTRF, and writes the reward to `/logs/verifier/reward.txt` where the harness reads it. Reward is 1 only when every row of every case passes.
