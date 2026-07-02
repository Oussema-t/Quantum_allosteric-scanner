# Resolution Vocabulary

## Purpose

Define canonical lifecycle and resolution terms so task and test-management commands do not overload one another.

## Task Lifecycle States

| State | Meaning |
|-------|---------|
| `proposed` | not yet accepted into active execution |
| `active` | currently being worked |
| `blocked` | cannot progress without an external dependency or decision |
| `resolved` | work reached a terminal outcome with an explicit resolution |
| `closed` | administratively completed after resolution |
| `deleted` | permanently removed from the backend |

## Task Resolution Values

| Resolution | Meaning |
|------------|---------|
| `done` | requested outcome completed as intended |
| `fixed` | specific defect corrected |
| `wont-do` | intentionally not pursued |
| `duplicate` | superseded by an existing task or ticket |
| `obsolete` | no longer relevant because context changed |
| `not-reproducible` | issue could not be reproduced with current evidence |
| `moved` | work transferred to another canonical task or backend |

## Managed Test Object Lifecycle

### Test Case States

- `draft`
- `ready`
- `implemented`
- `deprecated`
- `retired`

### Test Step States

- `draft`
- `active`
- `updated`
- `retired`

## Rules

- `/task-resolve` requires an explicit resolution value.
- `/task-delete` is permanent and must not be used for close, archive, or resolve semantics.
- Backend adapters may map these canonical values to local system-specific fields, but should not silently change their meaning.
- Testcase and teststep lifecycle should be managed independently from automation-code changes.