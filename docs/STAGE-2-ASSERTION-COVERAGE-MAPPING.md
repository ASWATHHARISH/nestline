# Stage 2 assertion coverage and evidence reconciliation

**Reconciled:** 11 September 2026
**Current pinned Stage 2 suite:** 122 assertions
**Historical remote record:** 141 assertions

The Stage 2 remote verification record truthfully reports that 141 assertions ran
at that earlier verification point. The repository does not contain the exact
141-assertion SQL source, so a one-to-one explanation of nineteen removed or moved
assertions cannot be reconstructed without inventing evidence.

The current tracked Stage 2 SQL file contains 122 assertions and now declares
plan(122). This makes any future accidental deletion fail pgTAP instead of
silently reducing the suite. The machine-readable inventory is
data/supabase/stage2-assertion-coverage.json.

## Current 122-assertion inventory

| Coverage group | Assertions |
|---|---:|
| Policy catalogue | 16 |
| Owner reads | 16 |
| Owner updates | 9 |
| Owner deletes | 9 |
| Owner special boundaries | 6 |
| Outsider reads | 16 |
| Outsider updates | 9 |
| Outsider deletes | 16 |
| Outsider private retrieval | 1 |
| Owner-only membership constraint | 1 |
| Dependency invalidation | 5 |
| Storage and lifecycle boundary | 6 |
| Demo workspace and reset | 12 |
| **Total** | **122** |

Later suites add 12 Stage 3 exit-hardening, 26 Stage 3 onboarding, 35 Stage 4
document and 11 Stage 4 API-role assertions. The current full database gate is
therefore 206 assertions.

The later 84 assertions are additional coverage. They are not presented as a
one-for-one destination for the unavailable nineteen historical Stage 2
assertions. The historical remote JSON remains unchanged as an audit record; all
current-status documents use the pinned 122 and combined 206 counts.
