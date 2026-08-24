# SEAM-0015 A `func_ligand` config value must resolve a real functional site — and a fallback seed must not be scored against the floor it shares a construction with

- units: `config/targets.yaml`'s `func_ligand` field (config) -> `labels.
  functional_indices` (resolution tiers: func_ligand-contact ->
  `active_site_uniprot` -> top-degree topological-proxy fallback) ->
  any active-site-seeded observable (`CTQW`, `GNM_corr_seed`, etc., library
  code) -> `baselines.degree_centrality` (one of the three proximity-floor
  baselines every scored verdict is checked against)
- invariant: (a) the active-site seed consumed by any scored observable must
  be a real functional site — `functional_indices`' own provenance must not
  be the last-resort top-degree fallback unless a target's own config
  explicitly opts in (`allow_topdegree_fallback: true`); (b) when a target
  *does* opt into the fallback tier, that target's seed is `top-5 highest-
  degree residues` **by construction** — the same quantity
  `baselines.degree_centrality` measures — so an observable seeded there and
  the degree-centrality floor it is checked against no longer constitute an
  independent comparison, and this must be visible in the target's own
  config/report, not silently absorbed into an apparently-ordinary floor
  check
- owner: [[TASK-0231]] (Done) — built `labels.assert_functional_provenance_
  allowed`, wired into `build_labels` itself (not just a test file), raising
  unless a target's config explicitly opts in; [[TASK-0216]] (Done) —
  discovered the defect (9 of 13 targets silently seeded at graph hubs, not
  active sites, including the register's one surviving positive)
- seam-test: `tests/test_config_integrity.py`
  (`TestConfigIntegrityFuncLigandResolves` — every real target's declared
  `func_ligand` checked against real, live-fetched holo `ligand_groups`;
  `TestLabelPipelineGoldenValues` — pocket/active-site size/provenance
  pinned per target; `TestGlucokinaseMutationGuarded` — the original
  TASK-0216 defect re-introduced and confirmed caught, fail-first
  demonstrated before the guard existed, then confirmed passing after)
- status: **VERIFIED**
- provenance: opened 2026-08-24 by [[TASK-0232]] (Architect/Planner registry
  pass, source: Bartosz, 2026-08-21 — *"So many tests added and no newer
  seams?"*). **Scope note**: the guard closes the *silent, undisclosed*
  case — the actual historical defect. It does not remove the circularity
  itself for a target that explicitly opts in (e.g. `CARDIAC_MYOSIN_TABLE1`,
  opted in by [[TASK-0231]] alongside a stale-comment fix) — that target's
  own diagnosis (`NO_SIGNAL_IN_APO`) already reflects the degraded
  seed, and the opt-in makes the choice visible in the config rather than
  hidden, which is what invariant (b) actually asks for: disclosure, not
  elimination of every fallback use.
