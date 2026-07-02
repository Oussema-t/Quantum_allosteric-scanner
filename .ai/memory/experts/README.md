# Expert Memory Stubs

Last Updated: 2026-06-25

Future role-specific memory should use this layout:

- `experts/<role>/session_memory.md`
- `experts/<role>/long_memory.md`

Rules:

- use `session_memory.md` for temporary working recall
- use `long_memory.md` for durable expert-local knowledge
- move cross-team truth into `../shared/`
- archive stale or superseded memory under `../archive/`
- add these files only when the role starts producing reusable knowledge