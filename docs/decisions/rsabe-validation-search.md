# RSABE External Validation: Dataset Search Findings

## Status

Superseded - 2026-07-19. The `rds07`/Pumas lead below was never pursued to
completion: the user provided direct access to Patterson SD, Jones B (2012)
*Pharmaceutical Statistics* 11(1):1-7 (DOI 10.1002/pst.498) instead, which
contains a complete worked FDA-method example (Table II, 51 real subjects)
with every intermediate number needed to validate an implementation. That
fixture is what `src/openpkflow/be/rsabe.py` and
`tests/validation/test_be_rsabe_reference.py` are pinned against. This note
is kept for the historical record and in case the `rds07` lead is useful for
a future, independent second fixture (e.g. to validate the sigma_wR-floor or
imbalanced-design edge cases that Table II does not exercise).

## Why this note exists

`HANDOFF.md` flags FDA partial-replicate RSABE as blocked on an external,
pinned, subject-level observed-data comparator. This session searched public
sources for a usable dataset + reference decision. Findings below.

## Candidates evaluated

### 1. `replicateBE::TRR.RTR.RRT` reference datasets (rds02, rds04, rds07, rds30) - most promising lead

- Source: Schutz H, Tomashevskiy M, Labes D, Shitova A, Gonzalez-de la Parra M,
  Fuglsang A. "Reference Datasets for Studies in a Replicate Design Intended
  for Average Bioequivalence with Expanding Limits." AAPS J. 2020;22:44.
- CRAN package `replicateBE`, GPL-3. Load with `data(rds07, package =
  "replicateBE")`; also shipped as CSV under `/extdata/`.
- rds02, rds04 are **real observed data** (rds04 = Patterson & Jones 2012,
  Pharm Stat 11(1):1-7, Table II; 51 subjects, TRR/RTR/RRT, balanced,
  complete, CVwR > 30%). rds07, rds30 are simulated (GMR fixed at 0.90).
- Caveat: the paper's published consensus numbers were computed for **EMA
  ABEL**, not FDA's linearized/scaled RSABE criterion, across seven ABEL
  implementations. Not directly usable as an FDA RSABE reference on its own.
- **Second, independent leg**: the Pumas.ai bioequivalence course (Unit 12,
  "Reference Scaling Part I") runs a full worked **FDA-style RSABE** example
  on a dataset named `SLTGSF2020_DS07` - the naming matches the Schutz et al.
  (2020) author initials and dataset numbering, strongly suggesting this is
  the same public-domain rds07 data run through FDA's method instead of
  ABEL. The tutorial publishes intermediate numeric values: CVwR = 34.23%
  (sigma_hat_R = 0.3329), Howe's approximate RSABE statistic = -0.06284,
  reference scaling constant = 0.7967, theta = 0.7966887118898779.
- If the DS07/rds07 identity is confirmed, this gives a public-domain,
  redistributable, real-design (simulated-data) partial-replicate dataset
  with an independently published FDA-style worked numeric result to
  reproduce - closing exactly the gap `HANDOFF.md` describes.
- Not yet done: (a) confirm DS07 subject count/design matches rds07 (360
  subjects, 3 sequences, GMR 0.90) beyond the naming coincidence, (b) pull
  the actual rds07 CSV and reproduce CVwR/Howe's-stat with `be/rsabe.py`'s
  formulas, (c) re-check redistribution terms in the AAPS J data-availability
  statement before committing the CSV into `tests/validation/data/`.

### 2. FDA product-specific BE guidances

- Rarely publish subject-level data; typically summary statistics or study
  design requirements only. Not promising as a from-scratch fixture source
  without further per-guidance checking.

### 3. Patterson & Jones (2012) original paper

- Paywalled (Wiley, `10.1002/pst.498`). May independently discuss FDA scaled
  criteria for its own Table II data (the same data as `rds04`), but content
  could not be confirmed without institutional access.

### 4. CRAN `PowerTOST`

- Validates RSABE design constants (scaling constant, regulatory switching
  CV) analytically; does not fit observed subject-level datasets end-to-end.
  Useful for cross-checking constants, not a subject-level fixture.

### 5. CRAN `ReplicateBE` (general)

- EMA ABEL-oriented as previously noted in `HANDOFF.md`; the `TRR.RTR.RRT`
  datasets above are the one part of this ecosystem that looks reusable for
  FDA-style validation, via the independent Pumas cross-check in candidate 1.

## Recommendation

Pursue candidate 1: pull `rds07` from `replicateBE`, implement/verify the
FDA RSABE formulas already documented in `be/rsabe.py` against it, and check
whether the reproduced CVwR (34.23%) and Howe's approximate statistic
(-0.06284) match the Pumas tutorial's published values. If they match, pin
`rds07` (with full citation to Schutz et al. 2020 and a note on the Pumas
cross-check) as the external validation fixture and promote `be/rsabe.py`
past `NOT_EVALUABLE`. If they don't match, or the DS07/rds07 identity
doesn't hold up, this candidate is exhausted and the search continues.
