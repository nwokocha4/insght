# Camera-Trap Diversity Literature Extraction

Extract reported values from the open-access data paper shipped at `/app/data/reference/zhao2026_camera_trap_diversity.pdf`. This is an extraction task: the numbers and citation facts must come from the PDF, not from a model, a web lookup, or a generic diversity calculation.

Write three CSV files under `/app/output`.

1. `/app/output/altitude_diversity.csv` with header `altitude_zone,cameras,shannon_weiner,pielou,simpson`. From Table 2, write one row for the low-altitude gradient and one for the mid-altitude gradient. Use `low` and `mid` in `altitude_zone`. Copy the printed numbers exactly as decimals with three digits after the point.
2. `/app/output/species_detections.csv` with header `species,independent_photos`. From Table 1, write the `Number of independent photos` for `reeves_muntjac` and `wild_boar`. Write counts as plain integers without thousands separators.
3. `/app/output/source_citation.csv` with header `field,value`. Write exactly four rows with `field` values `title`, `doi`, `year`, and `journal`. Take the title, DOI, publication year, and journal name from the first page of the paper.

Do not alter the source PDF. Run `python3 /app/solve.py`; it must create all three files. Numeric comparisons use a tolerance of `0.0001`; all strings must match the paper exactly. Missing, duplicate, or extra rows fail.

You have 28800 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
