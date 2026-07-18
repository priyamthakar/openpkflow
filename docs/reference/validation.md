# openpkflow.validation

Utility functions for cross-checking openpkflow output against reference values.

## Public API

| Symbol | Type | Description |
|--------|------|-------------|
| `pct_bias(observed, reference)` | function | Percent bias: `(obs - ref) / ref * 100` |
| `rmse(observed, reference)` | function | Root mean squared error |
| `within_pct(observed, reference, pct)` | function | True if `|pct_bias| <= pct` |

## Example

```python
from openpkflow.validation import pct_bias, within_pct

# Check that NCA-recovered CL is within 5% of true CL
true_cl = 5.0
recovered_cl = 5.12
print(pct_bias(recovered_cl, true_cl))    # 2.4
print(within_pct(recovered_cl, true_cl, pct=5.0))  # True
```

## Validation strategy

OpenPKFlow combines independent external comparators with analytical and internal
checks. Examples include PKNCA, NonCompart, Phoenix public outputs, PowerTOST,
`bootf2`, and R `stats::nls`, alongside exact closed-form PK profiles and
hand-checkable degenerate cases.

See the [validation matrix](../validation-matrix.md) for comparator scope and test
locations, and `VALIDATION.md` at the repository root for the detailed
test-to-reference map. Comparator agreement guards against calculation drift; it
does not by itself make OpenPKFlow a validated regulated system.
