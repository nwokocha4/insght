# Camera-Trap Diversity Estimation

Taxonomy: TB-Science domain `Science`, field `Ecology`; repository track `science-ecology` (camera-trap biodiversity monitoring).

Ecologist brief. The agent must read the governing method note and detector calibration sheet, choose a defensible operating point and estimator set for each site's count profile, and report per-site Shannon, Simpson and bias-corrected Chao estimates. The instruction deliberately withholds the numeric cutoff, species register and formula variants; those must be derived from the method authority and calibration evidence.

## Difficulty

The graded cases make four decisions observable, with each wrong choice moving a reported value far beyond the `0.0001` tolerance (measured margins in `authoring/evidence/trap_margins.json`):

1. **Operating point from calibration.** `detection_calibration.csv` places the largest rejected target confidence at `0.6362` and the smallest accepted target at `0.7631`. The method note requires the midpoint rounded to `0.05`, giving `0.70`. Lowering the cutoff to `0.50` counts the marginal frame in `graded_01`, moving its site from `n=4, S=2` to `n=5, S=3`. A solver that guesses a round number rather than reading the calibration sheet fails.
2. **Richness estimator for singleton-heavy data.** `graded_02` has `f1=2, f2=0`: the bias-corrected form gives `chao=5.0000` while the classic form is undefined. The agent must select the finite variant and justify it from the count profile.
3. **Simpson definition.** `graded_03` (counts `4,4,2,2`) distinguishes Gini-Simpson `D=0.7222` from inverse Simpson `3.6000`, a gap of `2.8778`.
4. **Shannon base.** `graded_04` (counts `6,2,1,1`) distinguishes natural-log `H=1.0889` from base-2 `1.5710`, a gap of `0.4821`.

`graded_05` carries three blank frames beside four detections and `graded_06` carries an empty site beside a single-detection site, so a program that misapplies the operating point or mishandles `n=0` fails visibly. Preprocessing is fixed by the method note to keep the classifier deterministic; it is not claimed as a scientific decision.

## Reference solution

`solution/solve.py` loads the named pretrained model, applies the method note's preprocessing, derives the operating point from the calibration bands, counts only calibrated species above that cutoff, and writes per-site rows using the selected estimators. It also writes `/app/output/method_choices.csv`, recording each choice with a short evidence-based justification. `solution/solve.sh` stages the reference and smoke-runs it on the settled cases. `authoring/provenance/reference_build/build_reference.py` regenerates the method PDF from the embedded pages.

## Verification

`tests/test_outputs.py` stages each graded case fresh under `/app`, runs the submitted `/app/solve.py` as an unprivileged user, keys every output row by `site_id` with order free, and checks both the estimate table and the decision record. `H`, `D`, and `chao` must match within `0.0001`; `n_det` and `S` must match exactly; each recorded choice and its justification cue must be present. `tests/expected.json` holds the oracle rows. `tests/test.sh` runs the suite, emits CTRF, and writes the reward to `/logs/verifier/reward.txt`. Reward is 1 only when every check on every case passes.
