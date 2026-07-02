# Test Report Triage Taxonomy

## Purpose

Provide a stable classification vocabulary for reading execution reports and deciding what is failing, why, and who should own the next step.

## Classification Table

| Class | Meaning | Typical Signals | Likely Next Owner |
|-------|---------|-----------------|-------------------|
| `product-bug` | the system under test appears to violate intended behavior | stable reproduction, assertion mismatch, consistent functional failure | product or Implementer depending on scope |
| `environment-drift` | environment configuration or deployed state diverged from expected baseline | wrong service version, missing secrets, changed routes, stale config | Explorer, environment owner, or platform owner |
| `data-drift` | required fixtures, seeded data, or reference entities no longer match assumptions | missing records, renamed entities, permission shifts tied to data | Explorer, data owner, or test-maintenance owner |
| `infrastructure-issue` | execution platform or supporting systems are failing independently of the intended behavior | cluster failures, network faults, runner startup failures, storage issues | platform or infrastructure owner |
| `automation-defect` | the test code or automation harness is wrong or outdated | selector breakage, invalid waits, stale assumptions, wrong assertions | Implementer or test-automation owner |
| `unclear-signal` | evidence is insufficient to classify confidently | partial logs, mixed failures, non-reproducible results | Test Report Reviewer or Explorer |

## Rules

- Use one primary class first.
- Add secondary context only after the primary class is clear.
- `unclear-signal` is valid and should not be forced into a more specific bucket.
- Triage should identify the next best debugging path, not only the label.