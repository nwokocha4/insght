# Camera-Trap Per-Site Diversity Estimation

Estimate per-site species diversity from camera-trap images. Method authority: `/app/data/reference/camtrap_diversity_method.pdf` together with `/app/data/reference/detection_calibration.csv`. This brief states case, file, and output mechanics; it deliberately does **not** restate the detector operating point, species register, or estimator forms. Read the method note and calibration sheet and make the selections they require.

Cases in `/app/data` (`reference/` excluded). Each case has `sites.csv` (roster) and `images/<site_id>/*.jpg`. Read `sites.csv` for `site_id` values; each roster site gets one output row.

Run the detector named in the method note with the preprocessing it prescribes, in eval mode under `torch.no_grad`. Derive the confidence operating point from the calibration sheet using the note's rule; a frame counts only when its top-1 class is in the calibrated species register and its softmax confidence meets that operating point. Frames outside the register, including blanks, add nothing.

For each site, choose and apply the diversity estimators specified by the method note for Shannon entropy, Simpson diversity, and bias-corrected richness. The staged sites differ in singleton and doubleton structure, so use the note's selection rule rather than a familiar textbook variant. Your program must also write a short decision record justifying those choices from the calibration evidence and the count profiles.

Degenerate: if `n = 0` report `S=0, H=0, D=0, chao=0`. Round `H`, `D`, `chao` half up to 4dp; `n`, `S` integers.

Run `python3 /app/solve.py`; write `/app/output/<case>_estimate.csv` with header `site_id,n_det,S,H,D,chao`; key `site_id`, row order free. Missing/duplicate/unknown/nonnumeric rows fail. `H`, `D`, `chao` tolerance `0.0001`; `n_det`, `S` exact. Also write `/app/output/method_choices.csv` with header `choice,value,justification` and one row each for `confidence_threshold`, `shannon`, `simpson`, `chao`; the required values and justification cues are given in the method note.

You have 28800 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
