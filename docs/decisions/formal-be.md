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

FDA partial-replicate 2x2x3 RSABE supports only TRR/RTR/RRT and is validated against
Patterson SD, Jones B (2012) *Pharmaceutical Statistics* 11(1):1-7, Table II
(DOI 10.1002/pst.498) — a real 51-subject worked FDA-method example. The implementation
(method-of-moments delta-hat/sigma-wR estimators, the FDA/Haidar linearized aggregate
criterion, and the Hyslop-Hsuan-Holder 2000 confidence-bound combination) reproduces
both of the paper's regulatory decisions. `NOT_EVALUABLE` is returned only when the
reference intra-subject CV is below the 30% RSABE threshold (standard ABE applies
instead), not as a blanket validation gate.

**Requires balanced sequence allocation** (equal subjects per TRR/RTR/RRT sequence).
The delta-hat method-of-moments estimator only cancels period effects under balance;
an unbalanced design (e.g. from unequal dropout) fails closed with `ValueError` rather
than silently returning a biased decision. Confirmed by code review: an unbalanced
30/10/5 allocation with a realistic period effect and a true GMR of 1.0 produced a
spurious delta-hat large enough to flip PASS/FAIL, undetected by the balanced Table II
fixture. Supporting genuinely unbalanced/dropout data would require implementing
Patterson & Jones's group-weighted method-of-moments formula (Section 1.1) instead of
the current per-subject mean, which is future work, not done here.

## Provenance

Implementation is clean-room: regulatory guidance, published formulas, and independently
generated reference outputs may be used. BioEqPy source, templates, and tests are not copied.
