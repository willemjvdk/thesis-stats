# Notebook 00 — Refactoring Plan & Execution Log

## Plan

### Pre-work: `src/data_loading.py` — create_papers() healthcare setting
Replace `mode().iloc[0]` (lines 216-222) with explicit logic:
- All arms agree → single label
- Arms disagree → "Mixed: A / B" (alphabetically sorted)
- 9 papers affected (1080, 1952, 2125, 2821, 3116, 4876, 5563, 5973, 6159)

### Section changes
| Old | New | Action |
|-----|-----|--------|
| Import cell | Import cell | Collapse `# ^` per-function comments → grouped module summary. Add hash + ROOT explanation text. Scrap separate markdown cell. |
| Data Flow header | Data Flow header | "four" → "five notebooks (00, 02–05)". "Feeds N03,N04,N05" → "Feeds all downstream notebooks." |
| Section 1 | Section 1 | Markdown: "65 in raw CSV → 64 after excluding 5108." Note arm-level. Remove stray duplicate comment from code source. |
| Section 2 | **DELETED** | Range checks removed. Renumber: 3→2, 4→3, 5→4, 6→5, 7→6, 8→7, 9→8, 10→9. |
| Section 3 | Section 2 | Remove redundant `print(f"{col}:")`. Add diagnosis recode note. Add "(arm-level)" to header. |
| Section 4 | Section 3 | Remove inline key listings. Add separate cell printing all unique keys per field (no 15-key cap). |
| Section 5 | Section 4 | No changes. |
| Section 6 | Section 5 | Remove stray exclusion cell (ee6261c7) — moves to Section 6. |
| Section 7 | Section 6 | **Major rework**: 4 code cells — (a) exclusion doc moved from S6, (b) create_papers + merge + summary, (c) arm N stats, (d) arm arm-N print. Markdown explains healthcare "Mixed" logic. |
| Section 8 | Section 7 | No changes. |
| Section 9 | Section 8 | Fix data dict types: time_* float→int. Add digital_literacy_possession/frequency/skills. Document healthcare mixed labeling. |
| Section 10 | Section 9 | Fix summary: "65 papers" → "64 (1 excluded)". Remove "1 paper missing year". Fix "02_representativeness" → "03". |
| Final cell | Final cell | Timestamp + schema hash only. Scrap figure mapping and "Next: Run..." |

---

## Downstream Impact

| Target | What uses it | Impact | Severity |
|--------|-------------|--------|----------|
| N03 cell ~3 | Arm-level `healthcare_setting_label` via `build_fig_corpus_combined()` | **None** — arm data unchanged | — |
| N03 cell ~15 | Paper-level `papers['healthcare_setting_label'].value_counts()` for summary pct | Now shows "Mixed: A / B" rows. Value counts will change (51→53 secondary, 9→4 primary, 4→0 community + 7 mixed). Code may break if it expects only 3 labels. | ⚠️ check |
| N03 cell ~18 | `papers['healthcare_setting']` loaded into ds_paper but never used (dead code) | No impact | — |
| `build_table_summary.py` line 55 | `papers['healthcare_setting_label'].value_counts()` | Same as N03 — sees mixed labels | ⚠️ check |
| N04 | Does not use healthcare_setting | No impact | — |
| N05 | Does not use healthcare_setting | No impact | — |
| N02 | Does not use healthcare_setting | No impact | — |
| N01 | Does not use healthcare_setting | No impact | — |

---

## Execution Log

### Run 1 — 2026-06-09

**N00**: ✓ Executed cleanly. Healthcare setting shows 47 secondary, 4 community, 4 primary, 4 Mixed Community/Primary, 3 Mixed Community/Secondary, 2 Mixed Primary/Secondary. Data dict updated correctly.

**N01**: ✓ Executed cleanly. No changes needed.

**N02**: ✓ Executed cleanly. No changes needed.

**N03**: ✓ Executed cleanly. Arm-level healthcare setting figure unaffected (uses arm data, not paper-level). Paper-level counts in build_fig4_combined use PROGRESS-Plus fields only (not healthcare setting) — no impact.

**N04**: ✗ Failed on first run — `NameError: name 'h3_data' is not defined` in results-ready cell. Fixed by building `h3_data` inline from `papers` DataFrame. Second execution: ✓ clean.

**N05**: ✓ Executed cleanly. No changes needed.

**build_table_summary.py**: ✓ Executed cleanly. Shows mixed labels correctly in healthcare setting counts. No code change needed — `value_counts()` handles new label values transparently.

---

## Breakages Found

| Notebook | Issue | Fix | Severity |
|----------|-------|-----|----------|
| N04 | Results-ready cell referenced `h3_data` which is not defined in N04 | Build `h3_data` from `papers` DataFrame inline | TRIVIAL — fixed in-place |
| N04 | Cell 26 (figure mapping) had literal `\n` in string causing SyntaxError | Replaced mangled cell with clean timestamp line | TRIVIAL — fixed in-place |

### Run 2 — 2026-06-09 (partial item fixes)
- Fix 1: Removed residual `# ^` per-function comment for `get_schema_hash`.
- Fix 2: Added "five notebooks" shared-code note to Data Flow header.
- Fix 3: Added "Or: 03_representativeness" to Summary section.
All 14 plan items now fully executed.

**Non-trivial fixes: none.**

## Verified Healthcare Setting Downstream

| Target | Actual impact | Status |
|--------|-------------|--------|
| `build_table_summary.py` | Picks up mixed labels via `value_counts()`. No code change needed. | ✓ Compatible |
| N03 corpus figure (Panel B) | Uses arm-level `healthcare_setting_label` — no mixed labels appear. | ✓ Unaffected |
| N03 `build_fig4_combined` | Uses PROGRESS-Plus fields only, not healthcare setting. | ✓ Unaffected |
| N04, N05 | Do not use healthcare setting. | ✓ Unaffected |

## Verified Key Outputs

```
N00 exclusion:  cov_nr=5108: >30% non-COPD participants (excluded by load_arms)
N00 mixed:      Mixed: Community / home-based / Primary care                        4
N04 H3:         Each additional equity domain reported was associated with a 0.047 change...
N05 Cook:       H1: 6 influential points (threshold=0.0625)
```

---

# Notebook 01 — Refactoring Plan & Execution Log

## Plan

### Pre-work: Path cleanup (shared with N02 + conversion scripts)

Move 10 files from `data/COPD_extraction_consistency_analysis/copd_validation_pipeline/data/`
to `data/raw/`, then move old directory tree to `data/stale/COPD_extraction_consistency_analysis/`.

**Files moved:**

| File | Used by |
|------|---------|
| `copd_v11.jsonl` | N01, N02 |
| `copd_v11_rerun1.jsonl` | N01 |
| `field_validation_mapping.csv` | N01, N02, `convert_tier3_spotcheck.py` |
| `prior_extraction_clean.csv` | N02 |
| `tier2_gold_standard.jsonl` | N02 |
| `tier3_filled.csv` | N02 |
| `covnr_year_country_copd.csv` | N00 via `src/data_loading.py` |
| `2026.04.07 COPD overzicht +componenten_wvdkedit.xlsx` | `preprocess_prior_extraction.py` |
| `random5.csv` | `convert_tier2_to_jsonl.py` |
| `random10.xlsx` | `convert_tier3_spotcheck.py` |

**Files updated:**

| File | Change |
|------|--------|
| `src/data_loading.py:27-34` | `COUNTRY_YEAR_RAW_PATH` → `DATA_RAW / "covnr_year_country_copd.csv"` |
| N01 Section 0 | `DATA_DIR` → `ROOT / "data" / "raw"` |
| N02 Section 0 | Same |
| `scripts/preprocess_prior_extraction.py:20-22` | `PIPELINE_DATA` → `ROOT / "data" / "raw"` |
| `scripts/convert_tier2_to_jsonl.py:17-19` | Same |
| `scripts/convert_tier3_spotcheck.py:22-26` | Same |

N00 unaffected — imports `COUNTRY_YEAR_RAW_PATH` from `src/data_loading.py`.

### Section changes

| Old | New | Action |
|-----|-----|--------|
| Import cell | Import cell | Collapse `# ^` per-function comments → grouped module summaries. Remove stray prepended comment before `# ── Setup ──`. Use `DATA_DIR = ROOT / "data" / "raw"`. Add markdown explaining the mapping file. |
| Section 1 | Section 1 | **Delete** duplicate re-load cell. Replace with validation check cell (warning prints, not asserts). |
| Section 2 | Section 2 | Markdown: explain 69→61 (8 `needs_discussion_*` fields EXCLUDED). Code unchanged. |
| Section 3 | Section 3 | Add `secondary_metric` + `secondary_value` to flagged fields printout. Markdown: explain this builds table, saves CSV, prints flagged fields worst-first. Append Section 4's `per_field.to_csv(...)` line. |
| Section 4 | **DELETED** | Merged into Section 3. Renumber: 5→4, 6→5. |
| Section 5 | Section 4 | Keep code unchanged. Markdown: explain feeds N03's `ambiguous_cov_nrs` for PROGRESS-Plus reporting. |
| Section 6 | **DELETED** | Summary removed. |
| Final cell | Final cell | Timestamp + analyzed/flagged count. |

---

## N01 Execution Log

### Run 1 — 2026-06-09

**Pre-work (path cleanup)**:
- Copied 10 files from old validation directory to `data/raw/`.
- Updated `src/data_loading.py`: `COUNTRY_YEAR_RAW_PATH` → `DATA_RAW / "covnr_year_country_copd.csv"`.
- Updated 3 conversion scripts: `PIPELINE_DATA` → `ROOT / "data" / "raw"`.
- Updated N01 + N02: `DATA_DIR` → `ROOT / "data" / "raw"`.
- Moved old directory to `data/stale/COPD_extraction_consistency_analysis/`.

**N01**: Rebuilt, executed cleanly. All section changes applied. Validation check prints (not hard asserts). 69→61 explanation in Section 2 markdown. Section 3 merged with 4 including secondary_metric. Section 5 kept with explanation of N03 feed. Section 6 deleted.

**All 6 notebooks re-executed**: ✓ No errors.

**Breakages**:

| Notebook | Issue | Fix | Severity |
|----------|-------|-----|----------|
| N01 (during rebuild) | Import cell deleted by duplicate-removal logic | Re-inserted import cell manually | TRIVIAL |
| N02 | Old `DATA_DIR` path after cleanup | String replacement to `data/raw` | TRIVIAL |

**Run 2 — 2026-06-09 (N01 cross-ref fixes):**
- Fixed Section 3 output table: shortened `secondary_metric` names (val_agree, pct_agree, na_concord) to prevent row wrapping.
- Fixed Section 4 markdown: added explanation of per_paper_one_na → N03 feed.
- Fixed: Final timestamp cell was accidentally deleted with Section 6 (summary). Re-added.

**Non-trivial fixes: none.**

---

# Notebook 02 — Refactoring Plan & Execution Log

## Pre-work: Mapping CSV fixes

| Field | Old | New | Reason |
|-------|-----|-----|--------|
| `arm` | `A_reference` | `EXCLUDED` | Structural identifier (control/treat1/treat2), no validation value. Still used in merge key. |
| `fev1_other` | `A_reference` | `no` | Never collected in prior extraction CSV. Old mapping had `no`; upgrade was a mistake. |

After these changes, eligible fields drop from 17 to 15 (14 A_reference + 1 B_triangulation), and all 15 are analyzed — no more mystery skips.

## Plan

| Old | New | Action |
|-----|-----|--------|
| Import cell | Import cell | Collapse `# ^` per-function comments → grouped module summaries. |
| Data Flow header | Data Flow header | "64 papers" (was "65"). |
| Tier 1 markdown | Tier 1 markdown | Fix stale Group A/B field list: `n` → Group A, only `healthcare_setting` in Group B. Note 64 papers. Add header explaining field selection from mapping CSV. |
| Tier 1 code cell 2 | Tier 1 code cell 2 | Add printout of eligible fields (field_name + tier1_prior_extraction + data_type_bucket) for manual cross-reference. |
| Tier 1 adjudication | Tier 1 adjudication | Add comment explaining `n_unique` may be less than 14 A_reference fields. |
| Tier 2 markdown | Tier 2 markdown | Expand header: note 61 non-excluded fields, 5-paper scope, undersampled flag. |
| Tier 2 code cells | Tier 2 code cells | Per-cell comments explaining pairing loop, one-NA collection, undersampled flag — novice-readable. |
| Final cell | Final cell | Remove "Next: Run 03…"; timestamp + tier counts only. Scratch thesis figure mapping scrap. |

**Run 2 additions (2026-06-09):**

| # | Action |
|---|--------|
| 1 | Escape `>` → `\>` in Tier 1 markdown (blockquote rendering bug on `>30%`) |
| 2 | Backtick-wrap individual Group A/B field names for visual clarity |
| 3 | Reorder B_triangulation print before eligible fields table |
| 4 | Clarify Section 0: "arm-rows across N papers", "field definitions (N needs_discussion_* helper fields excluded from all analyses)" |
| 5 | Rename dict keys: `prior_is_na` → `human_extraction_is_na`, `llm_is_na` → `llm_extraction_is_na`, `prior_value_raw` → `human_extraction_value_raw`, `llm_value_raw` → `llm_extraction_value_raw` (Tier 1) |
| 6 | Same rename for Tier 2: `gold_is_na` → `human_extraction_is_na`, `gold_value_raw` → `human_extraction_value_raw` |
| 7 | Tier 2 print: "61 fields across 5 papers (10 arms)" |
| 8 | Tier 3 markdown: explain 49 relevant fields (excluded: structural IDs, `_error_type`/`_correction_note` cols) |
| 9 | tier3_by_field: print "reported = arms where LLM extracted non-NA value" |
| 10 | Correction notes: show error type `[{minor/major/no_error}]` per entry |
| 11 | Cell 9 one-NA print labels: "LLM-NA" → "LLM extraction NA", "Prior-NA" → "Human extraction NA" |
| 12 | Tier 2 arm count: use `drop_duplicates()` (was counting field×arm rows, not arms) |
| 13 | Fix duplicate `field_name` in eligible table: `copy() + assign index` → `reset_index()` |

**Deferred to naming audit (ideas.md):** `na_llm`, `na_prior`, `llm_na_nrs`, `prior_na_nrs`, `one_na_llm_cov_nrs`, `one_na_prior_cov_nrs` — inconsistent prefixes post-rename.

---

# Notebook 03 — Refactoring Plan & Execution Log

## Plan

| Old | New | Action |
|-----|-----|--------|
| Import cell | Import cell | Collapse `# ^` per-function comments → grouped module summaries. Remove `wilson_ci` import. |
| Section 1 | Section 1 | Fix `PER_PAPER_NA_PATH`: add `/pipeline/` to path. |
| Section 2.1 | Section 2.1 | Print mean + SD alongside median in year stats. |
| Section 2.2 | Section 2.2 | Header explain multi-continent logic. Print continent *before* country. |
| Section 2.4 | Section 2.4 | Remove superfluous blank lines. |
| Section 3.2–3.3 | Section 3.2 + Section 3.3 | Split into two sections. Move SD/SE/CI educational markdown → Garbage Bin. |
| Section 3.4 | Section 3.4 | Text fixes: "Individual trials (jittered)", ref labels: "ECLIPSE (mean)", "Nijmegen CSI outpatient", "Nijmegen CSI rehabilitation". |
| Section 4.1 (two cells) | Section 4.1 (one cell) | Merge two code cells (PROGRESS-Plus + sex/gender audit). |
| Section 4.2–4.3 | Section 4.2 | Move Wilson CI explanation → Garbage Bin. Renumber 4.4 → 4.3. |
| Section 4.4 | **MARKDOWN NOTE** | Deferred: `build_fig4_combined()` requires equity_score from N04. Will integrate after N03+N04+N05 merge. |
| Section 5.1 | **UNCHANGED** | Left as-is — will be integrated during N03+N04+N05 merge. |
| All `wilson_ci()` calls | Simple proportion | Replace `wilson_ci(n, total)` with `n/total`. Drop `ci_lower`/`ci_upper` from rdf/dsd. |
| Appendices A/B/C | Garbage Bin | Combine under "kill your children" header with all old header texts. Delete duplicate and mangled cells (6 total). Keep 2 code cells generating Appendix A/B figures. |
| Final cell | Final cell | Timestamp + key counts only. |

## N02 Execution Log

### Run 1 — 2026-06-09

**Pre-work:**
- Mapping CSV: `arm` → `EXCLUDED`, `fev1_other` → `no`. Eligible fields: 17 → 15. All 15 analyzed (no more silent skips).
- Verified: 14 A_reference + 1 B_triangulation. 13 A_reference fields have disagreements (1 had zero).

**N02:** All changes applied:
1. Import cell: `# ^` → grouped module summaries.
2. Tier 1 markdown: stale field list fixed (`n` → Group A). Field selection header added.
3. Tier 1 code: eligible fields table printed for cross-reference.
4. Adjudication: comment explaining n_unique < 14.
5. Tier 2: expanded markdown + code annotated with paragraph-level comments.
6. Final cell: "Next: Run 03…" removed.

**Re-execution:** Clean. 15 fields, 0 skips.

| Issue | Fix | Severity |
|-------|-----|----------|
| `eligible[['field_name', ...]]` KeyError (field_name is index) | Copy index → column before selecting | TRIVIAL |

---

## N03 Execution Log

### Run 1 — 2026-06-09

**N03:** All changes applied:
1. Import cell: `# ^` → grouped summaries. `wilson_ci` removed.
2. Section 1: `PER_PAPER_NA_PATH` → `/pipeline/`. Ambiguous-NA now loads.
3. Section 2.1: Year stats print mean + SD.
4. Section 2.2: Header explains `get_continent()` logic. Continent before country.
5. Section 2.4: Blank lines removed.
6. Section 3.2/3.3: Split; old SD/SE/CI markdown → Garbage Bin.
7. Section 3.4: Labels fixed: "Individual trials (jittered)", "ECLIPSE (mean)", "Nijmegen CSI outpatient/rehab".
8. Section 4.1: Two cells merged.
9. Section 4.2–4.3: Renumbered. Wilson CI text → Garbage Bin.
10. Section 4.3 (was 4.4): `build_fig4_combined` → markdown note (needs N04 data; after merge).
11. Wilson CI removal: all 3 calls → simple `n/total`. `ci_lower`/`ci_upper` dropped.
12. Garbage Bin: Appendices combined. 5 deleted cells (dup headers, mangled mapping, orphaned SMD).

**Re-execution:** Clean after 5 fix rounds.

| Issue | Fix | Severity |
|-------|-----|----------|
| `build_fig4_combined(papers, arms, ...)` → TypeError (4 args) | Fixed to 2 args, then reverted to markdown note | TRIVIAL |
| Import cell lost `execution_count` | Re-added | TRIVIAL |

---

## N03+N04+N05 Merge → `03_analysis.ipynb` (2026-06-09)

### Pre-merge snapshot
- Copied 5 output CSVs to `outputs/tables/legacy/pre_merge/` for cross-comparison.

### Built notebook: 66 cells, 18 sections + Appendix
All construction via nbformat. Key deduplications:
- 15+ imports consolidated into one Section 0 cell
- `wilson_ci` removed (dead in N04, unused in charts)
- `compute_equity_scores()` called once in §5 (was 2x in N04+N05)
- Digital inclusiveness score computed once in §7 (was 2x in N04+N05)
- 4 regression models fit once in §§8–10; N05 §14 reuses via dict
- `build_fig4_combined(papers, arms)` called in §17 (resolves old placeholder)
- `build_fig6_combined(papers)` called in §7 (end-to-end narrative)

### Variable fixes
- N05 reloads (`arms = load_arms(...)`, `papers = pd.read_csv(...)`) removed
- `h3_model` refit in results table → uses `model_h3` from §10
- `compute_equity_scores` signature: `(arms, papers)` → `papers['equity_score']`
- ds_paper boolean columns merged onto papers before §7

### Archived
- N03 → `legacy/03_representativeness_depreciated_after_merge.ipynb`
- N04 → `legacy/04_inferential_hypotheses_depreciated_after_merge.ipynb`
- N05 → `legacy/05_sensitivity_analyses_depreciated_after_merge.ipynb`
- Old prose → `legacy/garbage_bin.md`
- Stale `fig4c_progress_plus_completeness.*` deleted

### Documentation updated
- README.md, AGENTS.md, ideas.md: `00 → 05` → `00 → 03`
- N04/N05 rows removed from README

### Validation
- All regression β/p/N match pre-merge (floating-point noise only: ~1e-14)
- Sensitivity tables S2, S3 match exactly
- S4 column names differ from old N05 (new: `beta_original`/`beta_clean`; old: `original_beta`/`refit_beta`) — functional data identical

---

## Surplus Cleanup (2026-06-09 cross-ref)

### N00

| # | Cell | Action | Reason |
|---|------|--------|--------|
| 1 | Cell 17 | Deleted | Arm-level N stats (mean/median/min/max) — descriptive, doesn't belong in Section 6 paper-creation flow |

### N03

| # | Cell | Action | Reason |
|---|------|--------|--------|
| 1 | Cell 6 (Section 2.1) | Removed 2 stale comment lines | "# Combined figure…" leftovers from when combined figure was in 2.1 before moving to 2.4 |
| 2 | Cell 27 (Section 4.2) | Fixed comment: removed "with Wilson CIs" | CIs removed in refactor, comment didn't match code |
| 3 | Cell 12 (Section 2.4) | Removed duplicate import of `build_fig_corpus_combined` | Already imported in Section 0 |
| 4 | Cell 35 (id: `subtext_3_5`) | Deleted | Duplicate Appendix A description — same text already in Garbage Bin |

Both notebooks re-executed cleanly.

---

## Post-Merge Fixes (2026-06-09)

### Pre-flight
- Installed `brokenaxes>=0.4.6` + added to `requirements.txt`

### Plotting fixes
- `src/plotting.py`: Removed "Individual trials (jittered)" side label from `trial_scatter_means()`
- `src/plotting.py`: Changed legend "Individual trial" → "Individual trials (jittered)"
- `src/plotting.py`: `add_axis_break()` diagonal `//` → zigzag `/\` pattern
- `src/aggregation.py`: Comment explaining scipy's `df=` parameter is degrees-of-freedom

### Notebook fixes
| # | Section | Action |
|---|---------|--------|
| 1 | 3.4 | Ref labels: "Nijmegen CSI outpatient" → "Nijmegen CSI outpatient (mean)", same for rehab |
| 2 | 4.1 | Removed sex/gender print lines (superfluous confirmation) |
| 3 | 5 | Deleted histogram plots. Moved `build_fig4_combined(papers, arms)` here from old §17 |
| 4 | 7 | Added markdown note: table abbreviated, full breakdown in CSV. Removed fig6a/6b histograms |
| 5 | 9 | Removed 2 cluster-robust SE cells (markdown + code) → `garbage_bin.md`. Restored primary H2 model-fitting code |
| 6 | 10 | "equity score (0–7)" → "modified PROGRESS-Plus composite score (0–9)"; "digital inclusiveness score (0–3)" → "digital inclusiveness score (0–5)" |
| 7 | 11 | Markdown updated to match §10 name changes |
| 8 | 13 | Compact display: abbreviated column names (w_mean, uw_mean, diff, etc.) |
| 9 | 14 | Fixed `influential_cov_nrs` from positional indices → actual cov_nr values |
| 10 | 17 | Deleted (content moved to §5) |
| 11 | 18 | Deleted (confirmation only) |

### Re-execution
Clean. All regression β/p/N match pre-merge. Cov_nr fix confirms actual paper IDs in influential exclusion.

### Deferred variable renames
See "Variable/Function Naming Audit" section below.

---

## Variable/Function Naming Audit (2026-06-09)

### Recommended renames (HIGH priority)

| Current | Suggested | Location |
|---------|-----------|----------|
| `pool_across_papers` | `weighted_mean_across_papers` | `src/aggregation.py` |
| `unweighted_mean_across_papers` | `simple_mean_across_papers` | `src/aggregation.py` |
| `paper_level_weighted_mean` | `arm_weighted_mean_per_paper` | `src/aggregation.py` |
| `aggregate_equity_reporting` | `classify_equity_reporting` | `src/aggregation.py` |
| `ds_paper` | `digital_strategy_flags` | `03_analysis.ipynb` §6 |
| `dsd` | `digital_strategy_summary` | `03_analysis.ipynb` §6 |
| `ds_fields` | `digital_strategy_fields` | `03_analysis.ipynb` §6 |
| `s2, s3, S4` | `sens_arm_vs_paper, sens_weighted, sens_influential` | `03_analysis.ipynb` §§12–14 |
| `run_a` (N02) | `llm_run` | `02_human_validation.ipynb` |
| `var_names` (×3) | `baseline_var_names` in §3.2; reuse in §3.4 | `03_analysis.ipynb` |

### N02 POOR names

| Current | Suggested |
|---------|-----------|
| `ona` | `one_na_df` |
| `fdf`, `frow` | `field_df`, `field_row` |
| `a_fields` | `group_a_fields` |
| `rdf` | `reporting_df` |
| `prop_comb` | `combined_proportion` |

### N01/N03 POOR names

| Current | Suggested |
|---------|-----------|
| `pp_na` | `progress_plus_one_na` |
| `pp_fields` | `progress_plus_fields` |
| `na_df` | `one_na_df` |
| `stable` / `stable_df` | `table_rows` |
| `ds_data` | Delete (inline into `digital_strategy_summary`) |

### Source file POOR names

| Current | Suggested | File |
|---------|-----------|------|
| `_norm_pct` | `_normalize_percentage_string` | `normalization.py` |
| `_clean_cat` | `_clean_category` | `normalization.py` |
| `lw`, `ms` | `line_width`, `marker_size` | `plotting.py` (forest plot loops) |
| `cy` | `country_year` | `data_loading.py:252` |

### Deferred to ideas.md (LOW risk, broader audit scope)

| Item | Reason |
|------|--------|
| `na_df` dual lifecycle (N01 vs N03) | Low risk — linear notebook execution |
| `a_vals`/`b_vals` local scope | Loop-local, different notebooks |
| `load_gold_standard` passthrough | Semantic alias, add docstring |
| `summary` dict reuse (§11 vs §16) | Sequential execution guards |
| `excl`/`equip`/`train`/`support` in §7 | Short but formula-syntax adjacent, clear in context |
| `rw` in PROGRESS-Plus loop | Recognizable as "row" in a loop |
| All `excl` string literals | In agreement.py, not variable names |

