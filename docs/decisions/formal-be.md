# Formal Bioequivalence Decision

## Status

Accepted - 2026-07-19.

## Decision

OpenPKFlow owns formal complete balanced 2x2 crossover ANOVA and, after external
validation, FDA partial-replicate 2x2x3 RSABE. The existing paired TOST API and
replicate screening helper remain separate, backwards-compatible workflows.

## Initial formal ANOVA scope

- Long-format input: subject, sequence, period, treatment, and one endpoint.
- Complete balanced TR/RT 2x2 crossover studies only.
- Fixed sequence, period, and treatment effects with subject nested in sequence.
- Formal treatment contrast, ANOVA source table, residual MSE, intra-subject CV,
  GMR, confidence interval, and BE decision.
- Incomplete, unbalanced, rank-deficient, or malformed studies fail closed.

## FDA RSABE gate

FDA partial-replicate 2x2x3 RSABE supports only TRR/RTR/RRT after a pinned external
reference fixture validates model fitting, sWR, upper confidence bound, point-estimate
constraint, fallback behavior, and final decision. Until then, the public formal RSABE
surface must return NOT_EVALUABLE rather than a PASS or FAIL decision.

## Provenance

Implementation is clean-room: regulatory guidance, published formulas, and independently
generated reference outputs may be used. BioEqPy source, templates, and tests are not copied.
