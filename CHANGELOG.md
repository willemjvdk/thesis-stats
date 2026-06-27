# Changelog

History of thesis-extraction (Apr 29 – May 9) and thesis-writing (May 11 – Jun 16),
merged into this repository on 2026-06-27.

## Unification (2026-06-27)
- Merged thesis-extraction into thesis-stats as the canonical public repo
- Removed Anthropic API support (OpenRouter-only)
- Consolidated data converters into `scripts/data_converters.py`
- Removed dead code from analysis src/ (`load_trials`, `SCHEMA_VERSION`)
- Added regression test suite (194 tests across extraction + analysis)
- Created shared modules: `src/extraction/types.py`, `src/extraction/llm_utils.py`, `src/shared/paths.py`, `src/shared/na_detection.py`
- Updated all import paths to `src.extraction.*` / `src.analysis.*` layout
- Output paths relocated to `notebooks/outputs/`

---

## thesis-extraction (Apr 29 – May 9, 2026)

### Features
- 2026-05-01 add OpenRouter eval pipeline (Option B)
- 2026-05-01 add `--skip-existing` flag to eval/compare.py
- 2026-05-01 save timing and token stats to `output/eval/stats/{cov_nr}.json`
- 2026-05-01 update DM prompt with `digital_strategy_*` fields
- 2026-05-04 prompt versioning, multi-prompt comparison, and OpenRouter token limit increase
- 2026-05-04 replace Anthropic with OpenRouter as default
- 2026-05-04 add `--source` argument for data selection
- 2026-05-04 add `--skip-existing` flag with interactive prompt
- 2026-05-04 add `--check-errors`, `--rerun-errors`, and `--max-reruns` flags
- 2026-05-05 DM production run (275 papers), fix error detection
- 2026-05-05 add `--parallel` and `--timeout` flags with enhanced logging
- 2026-05-05 add metadata to JSON output, validate_vocabulary.py, and `--check-version-drift` flag
- 2026-05-05 integrate sebbaflow_validator into eval/ — post-extraction validation with 4-layer checks
- 2026-05-06 CVD extraction (223 papers), fix URL overflow in markdown
- 2026-05-07 add arms extraction with two-pass pipeline
- 2026-05-08 DM rerun with corrected prompt
- 2026-05-09 final COPD rerun, error correction workflow

### Fixes
- 2026-05-02 raise MAX_TOKENS to 8192 for OpenRouter models
- 2026-05-02 correct COST_PER_M keys and prices for V4 models
- 2026-05-05 update tests to mock `get_output_dir` instead of `OUTPUT_DIR`
- 2026-05-06 fix URL overflow in markdown, TABLE_1 regex, cropped figures
- 2026-05-07 fix xurl for URL overflow

### Infrastructure
- 2026-05-01 add tests, pre-commit hook, coverage, and project docs
- 2026-05-04 refactor: add infrastructure improvements
- 2026-05-05 exclude sebbaflow_review from repo

---

## thesis-writing (May 11 – Jun 16, 2026)

### Features
- 2026-05-14 add full analysis pipeline: 5 Jupyter notebooks + 4 src modules
- 2026-05-14 add health/digital literacy reporting detection: `is_field_reported()` helper
- 2026-05-17 fix bitwise NOT bug; redesign digital inclusiveness score; add H2b cluster-robust SE
- 2026-05-17 add dual-bucket figures, arm-level setting tables, x-axis breaks
- 2026-05-18 replace fig3: dot plot with CI + SD comparison
- 2026-05-18 add forest plot as Option A alongside dot plot Option B
- 2026-05-19 implement pipeline infrastructure: unpack copd_validation into src/
- 2026-05-20 add Spearman correlation, TOC in N03, fig7 presentation variant
- 2026-05-21 add weighted mean aggregation, pooled within-trial SD
- 2026-05-22 add inter-run agreement module (Jaccard, token F1, exact match)
- 2026-05-23 add Gwet's AC1, ICC(2,1), Cohen's kappa, percent agreement
- 2026-05-24 add Bland-Altman summary, Wilson CI, NA concordance rate
- 2026-05-25 add normalization module (numeric, boolean, categorical, structured array, free text)
- 2026-05-26 add geography module (country-to-continent mapping)
- 2026-05-27 add loaders module (extraction output JSONL/JSON loaders)
- 2026-06-02 add 9 supplementary figures as 3 appendices
- 2026-06-04 add e-learning certificate appendix
- 2026-06-10 add regression tables (Table 2, Table 3)
- 2026-06-12 add digital inclusiveness score composite
- 2026-06-14 add equity reporting classification
- 2026-06-16 final polish: glossary updates, figure corrections

### Fixes
- 2026-05-17 fix `plt.show()` in `save_figure`; fix sample size cap 1500→1500
- 2026-05-18 restore old forest plot fig3_baseline_comparison
- 2026-05-20 fix xurl for URL overflow, TABLE_1 regex, cropped figures
- 2026-05-21 fix table1 footnote, PROSPERO cite
- 2026-06-02 fix search query (replaced hand-typed with original docx→PDF)
- 2026-06-10 fix regression table formatting
- 2026-06-14 fix equity score calculation edge cases

### Infrastructure
- 2026-05-13 add pre-commit hook system with 3-tier checks
- 2026-05-14 add LibreOffice lock warning to pre-commit hook
- 2026-05-17 add post-commit hook + sync script for secondary repo push
- 2026-05-19 separate AGENTS.md and EXECUTION_PLAN.md
- 2026-05-20 add AGENTS.md with 27-agent squad definition
- 2026-06-01 add requirements.txt for stats repo
- 2026-06-10 add validate_notebook.py and validate_notebooks.py scripts
- 2026-06-12 add data converter scripts (tier2, tier3, prior extraction)
