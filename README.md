# Camera-Trap Diversity Literature Extraction

Taxonomy: TB-Science domain `Science`, field `Ecology`; repository track `science-ecology` (camera-trap biodiversity monitoring). Task type: `EXTRACT`.

Literature-extraction brief. The agent receives one real, open-access data paper as a PDF and must recover reported tabular values and citation facts from it. The task does not train or run a classifier and does not ask for recomputed diversity indices; the graded answer is the published content itself.

## Source

Zhao W, Li M-M, Yan X-R, Zhang Z, Chen X-C, Chang Z-Q, Chen J-L, Ma J-J, Xu Z-P, Chen J-M, Lee PS, Zhang F (2026). “Camera trap survey of mammal diversity and activity rhythms of threatened species in a subtropical forest of Huangshan Mountain, China.” *Biodiversity Data Journal* 14: e184017. DOI `10.3897/BDJ.14.e184017`. CC BY 4.0.

The canonical PDF is kept in `authoring/evidence/` and copied into both the task image (`environment/data/reference/`) and the verifier image (`tests/reference/`) so the run is fully offline. No author-written method note or synthetic calibration sheet is shipped.

## Difficulty

The paper embeds its numbers in two dense tables. Table 2 reports altitude-stratified Shannon-Weiner, Pielou, and Simpson values that differ by only a few hundredths between zones, so an agent must locate the correct row and preserve the printed precision. Table 1 splits scientific names, common names, IUCN codes, and counts across wrapped lines; the Reeves's Muntjac count continues onto the following line after the species name. The citation fields require reading the first page rather than guessing a DOI or journal from the topic.

## Reference solution

`solution/solve.py` uses `pypdf` to extract text from the shipped PDF, applies anchored patterns to the Table 2 and Table 1 rows, reads the DOI, year, and title from the cover page, and writes the three required CSVs. `solution/solve.sh` stages the reference and smoke-runs it against the staged paper.

## Verification

`tests/conftest.py` stages the paper under `/app/data/reference/`, runs the submitted `/app/solve.py` as an unprivileged user, and loads the three output tables. `tests/test_outputs.py` checks headers, exact keys, decimal values within `0.0001`, and exact citation strings. `tests/expected.json` holds the values transcribed from the paper. `tests/test.sh` emits CTRF and writes the reward to `/logs/verifier/reward.txt`. Reward is 1 only when every check passes.
