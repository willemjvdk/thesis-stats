> **Status: All renames completed as of 2026-06-09. See commits `9e138a5` through `f6b80ad`.**

# Complete Variable & Function Naming Audit

> Generated 2026-06-08 from a full scan of 4 notebooks + 6 `src/` modules + 8 scripts.
> Goal: ensure every name describes what it does and no names overlap confusingly.

---

## Part A — Module Inventory

### `src/data_loading.py`

| Name | Kind | Context |
|------|------|---------|
| `ROOT` | constant | Project root, resolved from `__file__` |
| `DATA_MISC`, `DATA_RAW`, `DATA_PROCESSED`, `DATA_REFERENCES` | constants | Paths to data directories |
| `ARMS_PATH`, `PAPERS_PATH`, `COUNTRY_YEAR_PATH`, `COPD_CSV_PATH`, `COUNTRY_YEAR_RAW_PATH` | constants | Paths to specific data files |
| `SCHEMA_VERSION` | constant | Schema version string for tracking |
| `EXCLUDED_COV_NRS` | constant | Paper IDs excluded from corpus --- `COV_NRS` is opaque, but has docstring |
| `HEALTHCARE_SETTING_LABELS` | constant | Maps int codes to setting labels |
| `STRUCTURED_ARRAY_FIELDS` | constant | Field names using "Key: Value" format |
| `parse_structured_array(value)` | function | Parses "Key: Value~Key: Value" strings into list of (k, v) |
| `value_has_data(value)` | function | True if structured-array cell has meaningful content |
| `load_arms(path)` | function | Loads and validates arm-level CSV |
| `load_and_clean_country_year(path)` | function | Loads/cleans country/year lookup CSV |
| `create_papers(arms_df)` | function | Aggregates arm-level to paper-level DataFrame |
| `load_papers(path)` | function | Loads papers from CSV or creates from arms |
| `merge_year_country(papers_df)` | function | Merges country/year metadata into papers |
| `load_references(ref_dir)` | function | Loads reference cohort CSVs into nested dict |
| `get_schema_hash()` | function | SHA-256 hash of column schema for version tracking |

**Locals**: `p` (path), `df`, `cy` (country-year DataFrame), `h` (hash digest)

---

### `src/aggregation.py`

| Name | Kind | Context |
|------|------|---------|
| `_FIELD_REPORTED_VALUES` | constant | Which value means "reported" per field |
| `PROGRESS_PLUS_MAPPING` | constant | PROGRESS-Plus category to CSV column name(s) |
| `paper_level_weighted_mean(df, value_col, weight_col, group_col)` | function | N-weighted mean of a column grouped by paper ID |
| `pool_across_papers(papers_df, value_col, weight_col)` | function | Participant-weighted pooling across papers with optional 95% CI |
| `unweighted_mean_across_papers(papers_df, value_col)` | function | Simple (unweighted) mean across papers with optional 95% CI |
| `pooled_within_trial_sd(df, sd_col, n_col)` | function | Degrees-of-freedom-weighted pooled SD within trials |
| `aggregate_boolean_at_paper(arms_df, boolean_col)` | function | Aggregate arm-level booleans to paper (modal or any_true) |
| `is_field_reported(series, field_name)` | function | Check if a field value is meaningfully reported |
| `has_any_non_na_at_paper(arms_df, field_col)` | function | Check if any arm in a paper has data for a field |
| `aggregate_equity_reporting(arms_df, field_col, ambiguous_cov_nrs)` | function | Classify each paper as reported / not_reported / ambiguous |
| `compute_equity_scores(arms_df, papers_df, mapping)` | function | Compute 0--9 PROGRESS-Plus equity score per paper |

**Locals**: `valid`, `sums`, `values`, `weights`, `se` (standard error), `dfs` (degrees-of-freedom plural)

---

### `src/normalization.py`

| Name | Kind | Context |
|------|------|---------|
| `NORMALIZATION` | constant | Config dict controlling all normalization behaviour |
| `_NUMERIC_RE` | constant | Precompiled regex for extracting leading number from strings |
| `_is_na(value)` | function | Detect if a value should be treated as missing/NA |
| `normalize_value(value, bucket)` | function | Dispatch to the correct normalizer based on data-type bucket |
| `_normalize_string_basic(value)` | function | Whitespace + Unicode NFC normalization for strings |
| `_normalize_numeric(value)` | function | Coerce value to float, handling various number formats |
| `_normalize_categorical(value)` | function | Normalize categorical values (whitespace + NA, preserve case) |
| `_normalize_boolean(value)` | function | Coerce value to bool (True/False/1/0/yes/no) |
| `_normalize_structured_array(value)` | function | Decompose "Key: Value" strings into (key, value) tuples |
| `parse_prior_text(value, field_name)` | function | Parse prior free-text extraction into structured format |
| `_norm_pct(raw)` | function | Normalize a percentage string (comma to decimal dot) |
| `_clean_cat(cat)` | function | Strip and clean a category name from free text |
| `_normalize_free_text(value)` | function | Normalize free text (whitespace, Unicode, case, punctuation) |

**Locals**: `s` (ubiquitous for "string"), `m` (regex match), `num`, `val`, `cat`, `out`

---

### `src/plotting.py`

| Name | Kind | Context |
|------|------|---------|
| `PALETTE` | constant | Colorblind-safe colour palette (Wong 2011, 6 colours) |
| `BLUE`, `ORANGE`, `GREEN`, `RED`, `GRAY` | constants | Aliases for specific palette colours |
| `OUTPUT_DIR` | constant | Path to `outputs/figures/` |
| `lighten_hex(hex_color, factor)` | function | Lighten a hex colour by blending toward white |
| `save_figure(fig, name)` | function | Save figure as PDF and PNG to `outputs/figures/` |
| `bar_with_ci(...)` | function | Horizontal bar chart with CI whiskers |
| `scatter_with_regression(...)` | function | Scatter plot with LOWESS and OLS lines |
| `forest_plot(...)` | function | Forest-style plot with horizontal lines for estimates and CIs |
| `histogram_with_stats(...)` | function | Histogram with median, IQR, and optional annotation |
| `regression_diagnostics_plot(...)` | function | Residual + QQ + Cook's distance 3-panel diagnostic |
| `stacked_bar_crosstab(...)` | function | Single-panel stacked bar chart from crosstab |
| `stacked_bar_crosstab_dual(...)` | function | Dual-panel stacked bar chart (equal-width + phase buckets) |
| `forest_plot_means(...)` | function | 2x2 forest plot of cohort means with spread indicator |
| `add_axis_break(ax, axis)` | function | Add zigzag axis break marks for axes not starting at 0 |
| `_add_smd_threshold_bands(...)` | function | Add SMD threshold bands at +/-0.1, +/-0.25, +/-0.5 |
| `forest_plot_smd(...)` | function | Forest plot of SMD/Cohen's h comparing trial vs reference cohorts |
| `_setup_smd_panel(...)` | function | Draw a single SMD panel on an axes |
| `_forest_plot_smd_grid(...)` | function | 2x2 grid layout for SMD forest plot |
| `_forest_plot_smd_stacked(...)` | function | Single-panel stacked layout for SMD forest plot |
| `_beeswarm(...)` | function | Greedy beeswarm placement for non-overlapping y-offsets |
| `trial_scatter_means(...)` | function | 2x2 strip plot of per-trial means against reference cohort lines |

**Locals**: `lw` (line width), `ms` (marker size) in forest plot loops

---

### `src/agreement.py`

| Name | Kind | Context |
|------|------|---------|
| `THRESHOLDS` | constant | Per-bucket threshold dict (primary + secondary metrics with minimums) |
| `AgreementResult` | dataclass | Container: field_name, bucket, n_compared, n_both_na, n_one_na, primary_metric_*, secondary_metric_*, flagged, flag_reason, raw_disagreements, extra |
| `compute_agreement(field_name, bucket, paired_values)` | function | Main dispatch for per-field agreement analysis |
| `key_jaccard(...)` | function | Jaccard index on key sets across paired structured arrays |
| `value_agreement_on_matched_keys(...)` | function | Fraction of matched-key values that agree numerically or textually |
| `token_f1(...)` | function | Average token-level F1 across paired free-text strings |
| `exact_match_rate(...)` | function | Proportion of exactly matching pairs |

*(All names in this module are well-chosen --- no flags.)*

---

### `src/geography.py`

| Name | Kind | Context |
|------|------|---------|
| `CONTINENT_MAP` | constant | Country name to continent label mapping |
| `get_continent(country)` | function | Map country string to continent label |

*(Clean --- no flags.)*

---

### `src/statistics.py`

| Name | Kind | Context |
|------|------|---------|
| `cooks_distance(model)` | function | Cook's distance from fitted statsmodels regression model |
| `pearson_correlation(x, y)` | function | Pearson r with p-value |
| `vif_from_model(exog_df)` | function | Variance Inflation Factor from exogenous DataFrame |
| `compute_smd_table(...)` | function | Standardized Mean Differences table |

*(Clean --- no flags.)*

---

### `scripts/` (builders and converters)

**Imports from `src/` that would break if renamed:**

| `src/` symbol | Imported by |
|---------------|-------------|
| `save_figure` | `build_fig_corpus_combined_a.py`, `build_fig4_combined.py`, `build_fig6_combined.py` |
| `lighten_hex` | `build_fig_corpus_combined_a.py`, `build_fig4_combined.py`, `build_fig6_combined.py` |
| `get_continent` | `build_fig_corpus_combined_a.py` |
| `compute_equity_scores` | `build_fig4_combined.py` |
| `aggregate_equity_reporting` | `build_fig4_combined.py` |
| `aggregate_boolean_at_paper` | `build_fig6_combined.py` (standalone only) |
| `load_arms` | `build_fig6_combined.py` (standalone only) |

`convert_tier3_spotcheck.py`, `convert_tier2_to_jsonl.py`, `preprocess_prior_extraction.py`, `build_table_summary.py` have **zero** `src/` dependencies --- fully self-contained.

---

## Part B --- Notebook Inventories

### `00_data_validation.ipynb`

| Section | Key Names | Description |
|---------|-----------|-------------|
| \S0 Setup | `ROOT` (local `Path`) + `ROOT` (re-imported from `src.data_loading` --- shadows) | Project root, defined locally then overwritten by import |
| \S1 Load arms | `arms` (DataFrame, 134 rows), `c` (column loop), `na`/`na_pct` (missingness), `marker` (emoji string for >50% missing) | Validates arm-level data completeness |
| \S2 Categorical | `col` (loop over arm/diagnosis/setting) | Validates categorical field values |
| \S3 Structured arrays | `col`, `v` (raw value), `k` (key name), `parsed` (list of tuples) | Checks structured-array field contents |
| \S4 Arm counts | `arm_counts`, `extra` (multi-arm papers), `few` (malformed papers) | Validates arm count per paper |
| \S5 Country/year | `cy` (country/year DataFrame), `all_countries`, `c` (country loop) | Loads and validates country/year lookup |
| \S6 Build papers | `papers` (64 rows), `missing_year`, `missing_country` | Builds paper-level dataset |
| \S7 Save | `schema_file` (Path to schema_version.txt) | Saves processed data to CSV |
| \S8 Data dict | `dictionary_lines`, `field_descriptions`, `dict_path` (path to data_dictionary.md) | Generates data dictionary markdown |

---

### `01_inter_run_consistency.ipynb`

| Section | Key Names | Description |
|---------|-----------|-------------|
| \S0 Setup | `ROOT`, `DATA_DIR`, `run_a`/`run_b` (LLM extraction runs A and B), `mapping` | Loads two JSONL runs + field mapping |
| \S1 Validate | *(print-only --- uses existing names)* | Checks run consistency (row counts, cov_nr/arm overlap) |
| \S2 Agreement | `results` (list of AgreementResult), `per_paper_na`, `field_name`/`row`, `a_vals`/`b_vals` (run A/B data), `merged`, `paired`, `mr` (merged row) | Computes per-field inter-run agreement |
| \S3 Table | `rows`, `r` (agreement result loop), `per_field`, `flagged` | Builds per-field agreement table |
| \S4 N03 feed | `na_df` (one-NA DataFrame), `pp_fields` (PROGRESS-Plus field names), `pp_na` (PP subset), `subset`, `cov_list` | Compiles ambiguous-NA paper list for downstream |

---

### `02_human_validation.ipynb`

| Tier | Key Names | Description |
|------|-----------|-------------|
| \S0 Setup | `ROOT`, `DATA_DIR`, `run_a` (LLM run), `mapping`, `n_excluded` | Loads LLM run + field mapping + prior extraction |
| Tier 1 Load | `prior`, `eligible` (15 A_reference + B_triangulation fields), `eligible_print` | Loads prior human extraction, filters eligible fields |
| Tier 1 Agreement | `tier1_results`, `tier1_raw`, `tier1_one_na_detail`, `a_vals`/`b_vals` (LLM/prior), `merged`, `paired` | Computes LLM vs prior agreement per field |
| Tier 1 Table | `rows`, `r` (loop), `tier1_per_field`, `ona` (one-NA DF), `llm_list`/`prior_list` | Builds per-field Tier 1 results table |
| Tier 1 Queue | `a_fields` (Group A field names), `queue_rows`, `queue_df` (adjudication queue) | Builds adjudication queue for flagged fields |
| Tier 1 One-NA | `one_na_df`, `fdf` (field-NA subset), `na_llm`/`na_prior`, `llm_na_nrs`/`prior_na_nrs` | Details which papers have one-side NA |
| Tier 2 Agreement | `gold`, `tier2_results`, `tier2_raw`, `tier2_one_na_detail` | LLM vs gold standard (5 papers) |
| Tier 2 Table | `rows`, `r`, `tier2_per_field`, `ona` (\*shadows Tier 1 `ona`), `llm_list`/`gold_list` | Builds per-field Tier 2 results |
| Tier 2 Queue | `queue_rows`, `queue_df` (\*shadows Tier 1), `flagged2`, `frow` (flagged row), `us` ("[UNDERSAMPLED]" marker) | Tier 2 adjudication |
| Tier 3 | `tier3`, `error_cols`, `RELEVANT_FIELDS` (49-field set), `ERROR_TYPE_MAP`, `error_summary`, `tier3_by_field`, `has_errors` | Tier 3 spot-check error analysis |
| Summary | `g1_fields`/`g2_fields` (Group A/B fields), `combined` | Three-tier combined summary |

---

### `03_analysis.ipynb`

| Section | Key Names | Description |
|---------|-----------|-------------|
| \S0 Setup | `ROOT`, `ARMS_PATH`, `PAPERS_PATH`, `OUTPUT_TABLES`, `ALPHA` (dead), `MULTIPLE_TESTING_METHOD` (dead) | Imports all `src/` modules, sets paths |
| \S1 Load | `arms`, `int_arms` (treatment arms only), `papers` (64 rows), `refs` (reference cohorts), `ambiguous_na`, `na_df`/`pp_fields`/`pp_na` (from N01) | Loads arms, papers, references, ambiguous-NA |
| \S2.1 Year | `years` (publication year Series), `papers['continent']`, `papers['bucket_eq']`/`bucket_ph` (year buckets) | Year distribution histogram + continent column |
| \S2.2 Geography | `country_counts`, `cont_counts`, `geo_df` | Country and continent frequency tables |
| \S2.3 Sample | `trial_n`, `n_cutoff` (400), `n_outliers`, `pilot` (<30 N) | Sample size histogram + pilot trial flag |
| \S2.4 Setting | `arms_plot`, `setting_counts`, `setting_df` | Healthcare setting arm-level summary |
| \S2.5 Diagnosis | `classify_diagnosis()` (local function) | COPD-only vs COPD+other vs Unknown |
| \S3.1 Baselines | `baseline_cols` (4 fields --- \*redefined identically in \S12), `paper_baselines` | Per-paper n-weighted baseline means |
| \S3.2 Pooling | `pooled` (dict of stats), `p` (result dict), `stable`/`stable_df` (table rows), `var_names` (baseline var display map) | Participant-weighted pooling + comparison table |
| \S3.3 SD | `sd_fields`, `sd_comparison`, `ref_order`, `ref_labels_short`, `ref_colors` | Pooled within-trial SD vs reference SDs |
| \S3.3 (artifact) | **Cell 11 --- full duplicate setup block (120 lines)** | Merge artifact from legacy notebooks --- does nothing |
| \S4.1 PROGRESS-Plus | `PROGRESS_PLUS_FIELDS`, `reporting_data`, `rdf` (reporting DF), `prop_comb` (combined social capital proportion) | PROGRESS-Plus reporting completeness |
| \S5 Equity score | `papers['equity_score']` (0--9), `fig4` | Equity score distribution + Figure 4 |
| \S6 Digital | `ds_fields`/`ds_labels`, `ds_paper` (boolean flags), `ds_data` (summary rows), `dsd` (summary DF) | Digital strategy frequencies |
| \S7 Inclusiveness | `excl`/`equip`/`train`/`support` (boolean Series), `usable`, `score`, `fig6` | Digital inclusiveness score + Figure 6 |
| \S8 H1 | `valid_h1` (64 papers), `model_h1`, `beta`/`ci`/`p_val` | Equity score ~ publication year |
| \S9 H2 | `xr` (\*shadowed in \S10), `xr2`, `model_h2_age`, `model_h2_fev1`, `beta_age`/`beta_fev1` | Age / FEV1% ~ publication year |
| \S10 H3 | `r` (Pearson r), `r_p` (p-value), `vif`, `model_h3`, `model_h3_unadj`, `xr` (\*shadows \S9) | Digital inclusiveness ~ equity_score + year |
| \S11 Results | `results_rows`, `results_df`, `summary` (\*shadowed in \S16) | Compiled inferential results table |
| \S12 Sens1 | `baseline_cols` (\*redefined), `s2`, `p` (\*different input than \S3.2) | Arm-level vs paper-level pooled means |
| \S13 Sens2 | `s3`, `s3_display` | Weighted vs unweighted pooling comparison |
| \S14 Sens3 | `THRESHOLD`, `models`/`formulas`/`data_frames`, `results` (loop list), `cd`, `S4` (\*uppercase mismatch with s2/s3) | Cook's distance influential observation analysis |
| \S15 Statements | `h1_beta`/`h2a_beta`/`h3_beta` etc. (aliases) | Results-ready print statements |
| \S16 Export | `summary` (\*shadows \S11), `summary_df` | Trial-level summary CSV export |
| \S26 Appx A | `sd_var_names` (\*structurally identical to \S3.2's `var_names`) | Forest plot with SD whiskers |
| \S27 Appx B | `var_names` (reuses \S3.2's) | Forest plot with SE whiskers |

---

## Part C --- Cross-File Conflicts

### True collisions (same file, different scope --- latent bugs)

| Name | File | Location | Risk |
|------|------|----------|------|
| `summary` | `03_analysis.ipynb` | \S11 vs \S16 | If any cell between uses \S11's `summary` after \S16 runs, gets trial-stats dict instead of inferential results |
| `ona` | `02_human_validation.ipynb` | Tier 1 (cell 4) vs Tier 2 (cell 10) | Independent use per tier --- fine functionally, but confusing to read |
| `queue_rows`/`queue_df` | `02_human_validation.ipynb` | Tier 1 (cell 5) vs Tier 2 (cell 11) | Tier 1 values overwritten by Tier 2 --- functionally fine, but erased |
| `xr` | `03_analysis.ipynb` | \S9 vs \S10 | \S10 `xr` (partial regression x-values) overwrites \S9 `xr` (H2a regression line) --- benign since \S9's `xr` is not needed after \S9 |
| `ROOT` | `00_data_validation.ipynb` | \S0 (local) vs \S0 (re-import) | Local `ROOT` overwritten by `from src.data_loading import ROOT` --- identical value, but incorrect signal |

### Redefinition (same value, computed twice)

| Name | File | Location | Issue |
|------|------|----------|-------|
| `baseline_cols` | `03_analysis.ipynb` | \S3.1 (cell 8) + \S12 (cell 21) | Identical list `['age_mean','gender_pct_female','fev1_pct_mean','bmi_mean']` defined twice --- should be one constant or reused |
| `relevant_error_cols` | `02_human_validation.ipynb` | Tier 3 cell 14 + cell 15 | Identical computation in consecutive cells --- compute once and reuse |
| `sd_var_names` | `03_analysis.ipynb` | \S3.2 (`var_names`) + \S26 (`sd_var_names`) | Structurally identical dict redefined in Appendix A --- reuse \S3.2's variable |

---

## Part D --- Naming Quality Issues

### Critical --- dead code / merge artifact

| \# | Name | File | Problem | Fix | Done |
|----|------|------|---------|-----|------|
| C1 | Cell 11 entire block (120 lines) | `03_analysis.ipynb` | Duplicate setup --- re-imports all modules, redefines all paths. Merge artifact from legacy notebooks. | Delete cell | ✓ |
| C2 | `ALPHA` | `03_analysis.ipynb` \S0 | Defined as `0.05` but never referenced | Delete | ✓ |
| C3 | `MULTIPLE_TESTING_METHOD` | `03_analysis.ipynb` \S0 | Defined as `'none_exploratory'` but never referenced | Delete | ✓ |

### High --- abbreviation obscures meaning for a novice reader

| \# | Current Name | File | What It Means | Suggested Name | Done |
|----|-------------|------|---------------|----------------|
| H1 | ✓ | `pool_across_papers` | `src/aggregation.py` L37 | Participant-weighted pooling across papers | `weighted_mean_across_papers` |
| H2 | ✓ | `unweighted_mean_across_papers` | `src/aggregation.py` L98 | Simple (unweighted) mean across papers | `simple_mean_across_papers` |
| H3 | ✓ | `aggregate_equity_reporting` | `src/aggregation.py` L234 | Classifies paper as reported/not/ambiguous | `classify_equity_reporting` |
| H4 | ✓ | `paper_level_weighted_mean` | `src/aggregation.py` L14 | N-weighted mean grouped by paper | `arm_weighted_mean_per_paper` |
| H5 | ✓ | `ds_paper` | `03_analysis.ipynb` \S6 | Boolean DF for 4 digital strategies | `digital_strategy_flags` |
| H6 | ✓ | `dsd` | `03_analysis.ipynb` \S6 | Digital strategy summary table | `digital_strategy_summary` |
| H7 | ✓ | `ds_fields` | `03_analysis.ipynb` \S6 | Digital strategy field names | `digital_strategy_fields` |
| H8 | ✓ | `ds_labels` | `03_analysis.ipynb` \S6 | Digital strategy display labels | `digital_strategy_labels` |
| H9 | ✓ | `ds_data` | `03_analysis.ipynb` \S6 | List of digital strategy summary rows | Delete --- inline into `digital_strategy_summary` |
| H10 | ✓ | `pp_fields` | `01_inter_*.ipynb`, `03_analysis` | PROGRESS-Plus field names | `progress_plus_fields` |
| H11 | ✓ | `pp_na` | `01_inter_*.ipynb`, `03_analysis` | PROGRESS-Plus one-NA subset | `progress_plus_one_na` |
| H12 | ✓ | `na_df` | `01_inter_*.ipynb` \S4 | DataFrame of one-NA cases | `one_na_cases_df` |
| H13 | ✓ | `ona` | `02_human_*.ipynb` Tier 1 + 2 | One-NA detail DataFrame | `tier1_one_na_df` / `tier2_one_na_df` |
| H14 | ✓ | `fdf` | `02_human_*.ipynb` Tier 1 | Field-NA subset DataFrame | `field_one_na_cases` |
| H15 | ✓ | `frow` | `02_human_*.ipynb` Tier 2 | Flagged row in iteration | `flagged_row` |
| H16 | ✓ | `a_fields` | `02_human_*.ipynb` Tier 1 | Set of Group A field names | `group_a_field_names` |
| H17 | ✓ | `rdf` | `02_human_*.ipynb`, `03_analysis` \S4.1 | Reporting DataFrame (PROGRESS-Plus) | `reporting_df` |
| H18 | ✓ | `prop_comb` | `02_human_*.ipynb`, `03_analysis` \S4.1 | Combined proportion for social capital sub-fields | `combined_proportion` |
| H19 | ✓ | `g1_fields` / `g2_fields` | `02_human_*.ipynb` Summary | Tier 1 Group A / Group B fields | `tier1_group_a_fields` / `tier1_group_b_fields` |
| H20 | ✓ | `S4` | `03_analysis.ipynb` \S14 | Sensitivity 4 (influential observations) | `sens_influential` |
| H21 | ✓ | `s2` | `03_analysis.ipynb` \S12 | Sensitivity 2 (arm vs paper comparison) | `sens_arm_vs_paper` |
| H22 | ✓ | `s3` | `03_analysis.ipynb` \S13 | Sensitivity 3 (weighted vs unweighted) | `sens_weighted` |
| H23 | ✓ | `var_names` | `03_analysis.ipynb` \S3.2 | Baseline variable display labels + ref keys | `baseline_var_names` |
| H24 | ✓ | `stable` / `stable_df` | `03_analysis.ipynb` \S3.2 | Table rows / DataFrame for baseline comparison | `table_rows` / `baseline_table` |
| H25 | ✓ | `r_p` | `03_analysis.ipynb` \S10 | P-value of Pearson r | `pearson_p` |
| H26 | ✓ | `run_a` | `01_inter_*.ipynb`, `02_human_*.ipynb` | LLM extraction run A | `llm_run` |
| H27 | ✓ | `extra` | `00_data_*.ipynb` \S4 | Multi-arm papers (>2 arms) | `multi_arm_papers` |
| H28 | ✓ | `few` | `00_data_*.ipynb` \S4 | Malformed papers (<2 arms) | `malformed_papers` |
| H29 | ✓ | `cy` | `00_data_*.ipynb` \S5, `src/data_loading.py` L252 | Country/year DataFrame | `country_year_df` |
| H30 | ✓ | `dict_path` | `00_data_*.ipynb` \S8 | Path to data_dictionary.md | `data_dict_path` |
| H31 | ✓ | `marker` | `00_data_*.ipynb` \S1 | Emoji string for >50% missing | `missingness_marker` |

### Medium --- clarify with expand or rename

| \# | Current | File | Suggestion | Done |
|----|---------|------|------------|
| M1 | ✓ | `_norm_pct` | `src/normalization.py` L391 | `_normalize_percentage_string` |
| M2 | ✓ | `_clean_cat` | `src/normalization.py` L396 | `_clean_category` |
| M3 | ✓ | `lw` / `ms` (forest loop) | `src/plotting.py` L480, L510 | `line_width` / `marker_size` |
| M4 | ✓ | `summary` (two meanings) | `03_analysis.ipynb` \S11 vs \S16 | `inf_results` (\S11) / `trial_summary` (\S16) |
| M5 | ✓ | `sd_var_names` | `03_analysis.ipynb` \S26 | Delete --- reuse \S3.2's `baseline_var_names` |
| M6 | ✓ | `p` (result dict, diffferent inputs) | `03_analysis.ipynb` \S3.2 vs \S12 | \S12's renames to `pw` (paper-level weighted) or variable is inlined |
| M7 | ✓ | `results` (list in \S14) | `03_analysis.ipynb` \S14 | `sensitivity_results` |
| M8 | ✓ | `us` | `02_human_*.ipynb` Tier 2 | `undersampled_marker` ("us" reads as pronoun) |
| M9 | ✓ | `c` (loop var, multiple uses) | `00_data_*.ipynb` \S1, \S5 | `col_name` / `country_name` |
| M10 | ✓ | `v` (raw value loop) | `00_data_*.ipynb` \S3 | `raw_value` |

### Low --- acceptable but noted

| Name | File | Why acceptable |
|------|------|---------------|
| `r` (agreement result loop) | `01_inter_*`, `02_human_*` | Tight loop --- expanding to `result_item` not much clearer |
| `d` (disagreement dict loop) | `02_human_*` | Tight inner loop, 3-line scope |
| `mr` (merged row) | `01_inter_*`, `02_human_*` | 5-line loop scope, standard "merged row" abbreviation |
| `val_a`/`val_b` (raw values) | `01_inter_*`, `02_human_*` | Loop-local, clear in context |
| `h1_beta`/`h2a_beta` etc. | `03_analysis.ipynb` \S15 | Redundant aliases of \S8--\S10 variables --- convenient for results-ready statement cell |
| `EXCLUDED_COV_NRS` | `src/data_loading.py` | Has docstring, and `_COV_NRS` is explained in context. `EXCLUDED_PAPER_IDS` would be clearer but low priority |
| `_NUMERIC_RE` | `src/normalization.py` | Underscore prefix signals private; `RE` for "regex" is common in Python |
| `excl`/`equip`/`train`/`support` | `03_analysis.ipynb` \S7 | Tight cell-local scope, formula-like context --- clear to read |

---

## Part E --- Execution Plan

### Phase 1: Delete dead code (~5 min)

1. Delete Cell 11 (duplicate setup block, 120 lines) from `03_analysis.ipynb`
2. Delete `ALPHA` and `MULTIPLE_TESTING_METHOD` from `03_analysis.ipynb` \S0 import cell
3. Commit

### Phase 2: Source-only renames + script updates (~10 min)

| File | Rename |
|------|--------|
| `src/aggregation.py` | `pool_across_papers` \to `weighted_mean_across_papers` (L14, L37) |
| `src/aggregation.py` | `unweighted_mean_across_papers` \to `simple_mean_across_papers` (L73, L98) |
| `src/aggregation.py` | `paper_level_weighted_mean` \to `arm_weighted_mean_per_paper` |
| `src/aggregation.py` | `aggregate_equity_reporting` \to `classify_equity_reporting` (L75, L234) |
| `src/normalization.py` | `_norm_pct` \to `_normalize_percentage_string` (L391) |
| `src/normalization.py` | `_clean_cat` \to `_clean_category` (L396) |
| `src/plotting.py` | `lw` \to `line_width`, `ms` \to `marker_size` in forest plot loops |
| `src/data_loading.py` | `cy` \to `country_year_df` (L252) |
| `scripts/build_fig4_combined.py` | `aggregate_equity_reporting` \to `classify_equity_reporting` (L22) |
| `scripts/build_fig6_combined.py` | `aggregate_boolean_at_paper`, `load_arms` unchanged (standalone block) |

### Phase 3: Notebook local-scope renames (~20 min, nbformat)

All renames scoped to single cells --- no cross-cell breakage risk.

**`00_data_validation.ipynb`**

| Cell | Rename |
|------|--------|
| \S4 | `extra` \to `multi_arm_papers`, `few` \to `malformed_papers` |
| \S5 | `cy` \to `country_year_df` |
| \S8 | `dict_path` \to `data_dict_path` |
| \S1 | `marker` \to `missingness_marker` |

**`01_inter_run_consistency.ipynb`**

| Cell | Rename |
|------|--------|
| \S0 | `run_a` \to `llm_run` (also update `RUN_A_PATH` usage at load site) |
| \S4 | `na_df` \to `one_na_cases_df`, `pp_fields` \to `progress_plus_fields`, `pp_na` \to `progress_plus_one_na` |

**`02_human_validation.ipynb`**

| Cell | Rename |
|------|--------|
| \S0 | `run_a` \to `llm_run` |
| Tier 1 | `ona` \to `tier1_one_na_df`, `a_fields` \to `group_a_field_names`, `fdf` \to `field_one_na_cases` |
| Tier 2 | `ona` \to `tier2_one_na_df`, `frow` \to `flagged_row`, `us` \to `undersampled_marker` |
| Summary | `g1_fields` \to `tier1_group_a_fields`, `g2_fields` \to `tier1_group_b_fields` |

**`03_analysis.ipynb`**

| Cell | Rename |
|------|--------|
| \S1 | `na_df` \to `one_na_cases_df`, `pp_fields` \to `progress_plus_fields`, `pp_na` \to `progress_plus_one_na` |
| \S3.2 | `var_names` \to `baseline_var_names`, `stable` \to `table_rows`, `stable_df` \to `baseline_table` |
| \S4.1 | `rdf` \to `reporting_df`, `prop_comb` \to `combined_proportion` |
| \S6 | `ds_paper` \to `digital_strategy_flags`, `dsd` \to `digital_strategy_summary`, `ds_fields` \to `digital_strategy_fields`, `ds_labels` \to `digital_strategy_labels`, `ds_data` \to delete (inline list) |
| \S10 | `r_p` \to `pearson_p` |
| \S11 | `summary` \to `inf_results` |
| \S12 | `s2` \to `sens_arm_vs_paper` |
| \S13 | `s3` \to `sens_weighted` |
| \S14 | `S4` \to `sens_influential`, `results` \to `sensitivity_results` |
| \S16 | `summary` \to `trial_summary` |
| \S26 | Delete `sd_var_names`, reuse \S3.2's `baseline_var_names` in `forest_plot_means()` call |
| \S27 | `var_names` \to `baseline_var_names` (cosmetic --- already correct reference) |

### Phase 4: Cross-file import updates (~15 min, nbformat + scripts)

Update all call sites after Phase 2 function renames:

| Notebook/Script | Section | Old Call | New Call |
|-----------------|---------|----------|----------|
| `03_analysis.ipynb` | \S0 imports | `from src.aggregation import ... pool_across_papers` | `weighted_mean_across_papers` |
| `03_analysis.ipynb` | \S0 imports | `... unweighted_mean_across_papers` | `simple_mean_across_papers` |
| `03_analysis.ipynb` | \S0 imports | `... aggregate_equity_reporting` | `classify_equity_reporting` |
| `03_analysis.ipynb` | \S3.2 | `pool_across_papers(paper_baselines, ...)` | `weighted_mean_across_papers(paper_baselines, ...)` |
| `03_analysis.ipynb` | \S3.2 | `unweighted_mean_across_papers(paper_baselines, ...)` | `simple_mean_across_papers(paper_baselines, ...)` |
| `03_analysis.ipynb` | \S4.1 | `aggregate_equity_reporting(arms, ...)` | `classify_equity_reporting(arms, ...)` |
| `03_analysis.ipynb` | \S12 | `pool_across_papers(papers, ...)` | `weighted_mean_across_papers(papers, ...)` |
| `03_analysis.ipynb` | \S13 | `unweighted_mean_across_papers(papers, ...)` | `simple_mean_across_papers(papers, ...)` |
| `scripts/build_fig4_combined.py` | L22 | `aggregate_equity_reporting` | `classify_equity_reporting` |

### Phase 5: Re-execute all 4 notebooks, validate integrity

```bash
jupyter nbconvert --to notebook --execute --output-dir=notebooks notebooks/00_data_validation.ipynb
jupyter nbconvert --to notebook --execute --output-dir=notebooks notebooks/01_inter_run_consistency.ipynb
jupyter nbconvert --to notebook --execute --output-dir=notebooks notebooks/02_human_validation.ipynb
jupyter nbconvert --to notebook --execute --output-dir=notebooks notebooks/03_analysis.ipynb
python3 scripts/validate_notebooks.py notebooks
```

Verify: H1 beta = -0.055, H2a beta = -0.125 (unchanged).

### Phase 6: Commit

---

Summary

| Category | Count |
|----------|-------|
| Dead code items to delete | 3 |
| Source-only renames | 8 |
| Notebook local renames | 42 |
| Cross-file import updates | 9 |
| Pass (no rename needed) | ~150 |
| Affected files | `03_analysis.ipynb`, `02_human_*.ipynb`, `01_inter_*.ipynb`, `00_data_*.ipynb`, `src/aggregation.py`, `src/normalization.py`, `src/plotting.py`, `src/data_loading.py`, `scripts/build_fig4_combined.py` |
| Risk | Moderate --- source function renames (Phase 2) require careful cross-file tracking (Phase 4) |

---

## Execution Log

### Phase 1 — Dead code deletion (2026-06-08)

- **C1**: Deleted Cell 23 (was Cell 11 with old indexing) — duplicate setup block (4,474 chars). All imports already present in Cell 2.
- **C2**: Deleted `ALPHA = 0.05` from Cell 2.
- **C3**: Deleted `MULTIPLE_TESTING_METHOD = 'none_exploratory'` from Cell 2.
- **Re-execution**: Clean. H1 β=-0.055, p=0.3393. H2a β=-0.125, p=0.2168. All unchanged.
- **Commit**: 2578ad1

### Phase 2 — Source renames + notebook imports (2026-06-09)

- **H1**: `pool_across_papers` → `weighted_mean_across_papers` (`src/aggregation.py` L37, + 7 call sites)
- **H2**: `unweighted_mean_across_papers` → `simple_mean_across_papers` (`src/aggregation.py` L98, + 4 call sites)
- **H3**: `aggregate_equity_reporting` → `classify_equity_reporting` (`src/aggregation.py` L234, + 7 call sites)
- **H4**: `paper_level_weighted_mean` → `arm_weighted_mean_per_paper` (`src/aggregation.py` L14, + 1 call site)
- **M1**: `_norm_pct` → `_normalize_percentage_string` (`src/normalization.py`, 9 occurrences)
- **M2**: `_clean_cat` → `_clean_category` (`src/normalization.py`, 7 occurrences)
- **M3**: `lw` → `line_width`, `ms` → `marker_size` (`src/plotting.py` L514-518)
- **H29**: `cy` → `country_year_df` (`src/data_loading.py` L252)
- **Script**: `scripts/build_fig4_combined.py` — `aggregate_equity_reporting` → `classify_equity_reporting` (3 occurrences)
- **Re-execution**: All 4 notebooks clean. H1 β=-0.055, p=0.3393. H2a β=-0.125, p=0.2168.
- **Commit**: 2beb398

### Phase 3 — Notebook local renames (2026-06-09)

- **H5–H9**: `ds_*` → `digital_strategy_*` (17 occurrences in §6). `ds_data` kept as `digital_strategy_rows` (Option B).
- **H10–H12**: `pp_fields`/`pp_na`/`na_df` → `progress_plus_fields`/`progress_plus_one_na`/`one_na_cases_df` (N01 §4, N03 §1).
- **H13–H15**: `ona` → `tier1_one_na_df` (Tier 1) / `tier2_one_na_df` (Tier 2), `fdf` → `field_one_na_cases`, `frow` → `flagged_row`.
- **H16–H19**: `rdf` → `reporting_df`, `prop_comb` → `combined_proportion`, `g1_fields`→`tier1_group_a_fields`, `g2_fields`→`tier1_group_b_fields`.
- **H20–H22**: `s2`→`sens_arm_vs_paper`, `s3`→`sens_weighted`, `S4`→`sens_influential` (also fixed in §15 results-ready cell).
- **H23–H24**: `var_names`→`baseline_var_names`, `stable`→`table_rows`, `stable_df`→`baseline_table`.
- **H25–H28**: `r_p`→`pearson_p`, `extra`→`multi_arm_papers`, `few`→`malformed_papers`.
- **H29**: `cy`→`country_year_df` (N00 §5, already done in Phase 2 for src/).
- **H30**: `dict_path`→`data_dict_path`.
- **H31**: `marker`→`missingness_marker`.
- **M4**: `summary`→`inf_results` (§11) / `trial_summary` (§16).
- **M5**: `sd_var_names`→`baseline_var_names` (reuse §3.2's dict in Appendix A).
- **M7**: `results`→`sensitivity_results` (§14 loop).
- **M8**: `us`→`undersampled_marker`.
- **H26**: `run_a`→`llm_run` (N01+N02).
- **Snag**: `S4` missed in §15 results-ready cell — caught during re-execution, fixed in separate commit.
- **Re-execution**: All 4 notebooks clean. H1 β=-0.055, p=0.3393. H2a β=-0.125, p=0.2168.
- **Output diff**: CSV values match pre-merge within floating-point noise (~1e-15).
- **Commits**: 9d6916d (Phase 3) + 49826c0 (fix)

### Completion Summary (2026-06-09)

| Phase | Items | Commit |
|-------|-------|--------|
| 1. Dead code | 3 deleted | 2578ad1 |
| 2. Source renames | 8 src/ + 1 script + 9 import call-sites | 2beb398 |
| 3. Notebook renames | 42 local renames across 4 notebooks | 9d6916d |
| Fix | 1 missed `S4` in §15 | 49826c0 |

**Verification**: All 4 notebooks execute clean. Regression values unchanged from pre-rename:
H1 β=-0.055, p=0.3393. H2a β=-0.125, p=0.2168. Output CSVs diff at floating-point noise only.

**Remaining items** (acceptable, no rename needed):
- `excl`/`equip`/`train`/`support` — tight cell-local scope, formula-like context. Supervisor can read inline.
- `EXCLUDED_COV_NRS` — has docstring, explained in context.
- `_NUMERIC_RE` — private convention with underscore prefix.
