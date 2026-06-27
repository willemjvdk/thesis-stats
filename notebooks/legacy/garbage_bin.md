# Garbage Bin — Discarded Prose from Notebook Refactoring & Merge

Preserved for reference only. No executable code here.
The original notebooks are in `notebooks/legacy/*_depreciated_after_merge.ipynb`.

---

## From N03 Garbage Bin

### Old Section 3.2–3.3 educational content (SD/SE/CI)

**Standard Deviation (SD)** measures the spread of individual patients around
their mean. For each trial arm we have a reported SD; we combine them into a
*within-trial pooled SD* using degrees-of-freedom weighting (the meta-analytic
formula). This gives a patient-level quantity comparable to what reference
cohorts report. SD does not shrink with larger samples — it measures spread of
individuals, not precision of estimates.

**Standard Error (SE)** is the precision of the *mean* estimate: SE = SD / √n.
Larger n → smaller SE → more precise mean. A cohort with n=2000 and SD=15 has
SE ≈ 0.34; one with n=200 and the same SD has SE ≈ 1.06. Same patient spread,
very different precision.

| Quantity | What it measures | Shrinks with n? |
|----------|-----------------|-----------------|
| SD | Patient-level spread | No |
| SE | Precision of the mean | Yes (SE = SD / √n) |

**Confidence Interval (CI)** is a range around an estimate intended to capture
the true parameter in 95% of repeated samples (if the analysis were run many
times). For a mean: 95% CI ≈ mean ± 1.96 × SE. A narrow CI = precise estimate;
a wide CI = imprecise estimate.

> **How to read overlap:** CIs that overlap between the trial pool and a
> reference cohort are *suggestive* of comparability, but overlap of two 95% CIs
> does **not** directly map to "no statistical difference." The comparison is
> descriptive, not a formal test.

In the table below, each baseline variable shows:
- **Trial pool** — participant-weighted mean, 95% CI, and pooled SD
- **Reference cohorts** — mean, 95% CI (computed from their reported n and SD), and reported SD

### Old Section 4.2–4.3 Wilson CI explanation

**Wilson confidence interval** is a method for computing CIs on proportions that
is more accurate than the simple "mean ± 1.96 × SE" approach, especially at
small sample sizes or extreme proportions (near 0% or 100%).

For each PROGRESS-Plus variable we compute:
- **n_reported** / 65 papers → proportion
- **Wilson 95% CI** around that proportion

The Wilson interval behaves sensibly at boundaries: near 0% or 100%, the
simple Wald interval becomes pathologically narrow (0% ± 0%), while the
Wilson interval correctly widens to reflect the uncertainty of a rare or
near-ubiquitous event.

We also note the **number of arms** alongside the paper-level count, since
multi-arm trials contribute multiple observations within the same paper.

### Old Appendix figure notes

**Appendix Figure A:** Dots represent mean estimates; whiskers show patient-level
spread (mean ± 1.96 × SD), covering ~95% of individuals within each cohort, not
precision of the mean estimate. Abbreviations: OP = outpatient; PR = pulmonary
rehabilitation; DSP = disease-specific programme. The blue Trial pooled row is
drawn thicker to distinguish it from the reference cohorts.

**Appendix Figure B — Baseline cohort comparison (SE-CI):** Dots represent mean
estimates; whiskers show 95% confidence intervals. Reference cohorts (ECLIPSE,
Adelphi DSP, Nijmegen CSI outpatient group, Nijmegen CSI rehabilitation group)
have very large sample sizes (N=131–2876), so their CIs are too narrow to appear
as visible whiskers at this scale. The blue Trial pooled row is drawn with a
thicker line and larger marker to distinguish it from the reference cohorts.

**Appendix Figure C — SMD representativeness:** Dots represent standardized mean
differences (trial mean − reference mean) divided by the pooled standard deviation.
Positive values indicate trials enrolled patients with higher values than the
reference cohort; negative values indicate lower values. Shaded bands show
conventional covariate-balance thresholds: ±0.1 (negligible), ±0.25 (acceptable),
and ±0.5 (moderate). For the % Female row, the metric is Cohen's *h* (not SMD),
because no within-trial SD is available for a proportion variable.

---

## Old thesis figure mapping comments

These were removed per notebook conventions (AGENTS.md: final cells = timestamp + key counts only).

### From N03:
- `fig1a_corpus_combined → Figures 3a/3b (corpus composition)`
- `fig5_smd_grid → Figure 5 (SMD — removed, no longer generated)`

### From N04:
- `→ Thesis Figures 6 and 7` (equity + digital inclusiveness distributions)
- `→ Thesis Figure 8` (digital inclusiveness)

---

*Generated 2026-06-09 during N03+N04+N05 → 03_analysis merge.*


---

## Cluster-Robust SE (removed from Section 9, 2026-06-09)


### From markdown cell

**Arm-level sensitivity with cluster-robust SEs**

The primary H2 runs at paper-level (one mean per trial). The arm-level sensitivity
uses each arm as an observation.

**Why this matters:** multi-arm trials contribute 2+ mean ages. The arm-level
analysis increases observations and captures within-trial variation (e.g.,
treatment arm younger than control). However, arms within a trial share inclusion
criteria and protocol, so their ages are correlated — violating the OLS
assumption of independent observations.

**Cluster-robust standard errors** (sandwich estimator) adjust for this
non-independence by allowing errors to be correlated within `cov_nr` clusters.
- If arms within a trial are near-identical → cluster SE ≈ paper-level SE
- If arms differ (different populations per arm) → arm-level estimates diverge

The trade-off: the cluster estimator is asymptotically justified (needs *many*
clusters). With 59 clusters, we are at the borderline where cluster SEs can be
unreliable (Cameron & Miller 2015). The paper-level result is primary; the
arm-level result is a sensitivity check, reported cautiously.


### From code cell

# H2: Have enrolled populations changed over time?
# H2a: age_mean ~ year. H2b: fev1_pct_mean ~ year.
# Arm-level sensitivity uses cluster-robust SEs (arms within trial
# not independent). n_clusters=59, borderline reliable.
# H2a: age over time
valid_age = papers[['age_mean', 'publication_year']].dropna()
model_h2_age = smf.ols('age_mean ~ publication_year', data=valid_age).fit()
beta_age = model_h2_age.params['publication_year']
ci_age = model_h2_age.conf_int().loc['publication_year']
p_age = model_h2_age.pvalues['publication_year']
print(f"H2a: Mean age vs year")
print(f"  beta = {beta_age:.3f} [{ci_age[0]:.3f}, {ci_age[1]:.3f}], p = {p_age:.4f}, n = {len(valid_age)}")

# H2b: FEV1% over time
valid_fev1 = papers[['fev1_pct_mean', 'publication_year']].dropna()
model_h2_fev1 = smf.ols('fev1_pct_mean ~ publication_year', data=valid_fev1).fit()
beta_fev1 = model_h2_fev1.params['publication_year']
ci_fev1 = model_h2_fev1.conf_int().loc['publication_year']
p_fev1 = model_h2_fev1.pvalues['publication_year']
print(f"H2b: FEV1% predicted vs year")
print(f"  beta = {beta_fev1:.3f} [{ci_fev1[0]:.3f}, {ci_fev1[1]:.3f}], p = {p_fev1:.4f}, n = {len(valid_fev1)}")

# Scatter plots
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

ax1.scatter(valid_age['publication_year'], valid_age['age_mean'], color=BLUE, alpha=0.7)
add_axis_break(ax1)
xr = np.linspace(valid_age['publication_year'].min(), valid_age['publication_year'].max(), 50)
ax1.plot(xr, model_h2_age.params['Intercept'] + model_h2_age.params['publication_year'] * xr, color=RED, linewidth=2)
ax1.set_xlabel('Publication Year'); ax1.set_ylabel('Mean Age (years)')
ax1.set_title('H2a: Trial Mean Age over Time', fontweight='bold')
ax1.xaxis.set_major_locator(MaxNLocator(integer=True))

ax2.scatter(valid_fev1['publication_year'], valid_fev1['fev1_pct_mean'], color=GREEN, alpha=0.7)
add_axis_break(ax2)
xr2 = np.linspace(valid_fev1['publication_year'].min(), valid_fev1['publication_year'].max(), 50)
ax2.plot(xr2, model_h2_fev1.params['Intercept'] + model_h2_fev1.params['publication_year'] * xr2, color=RED, linewidth=2)
ax2.set_xlabel('Publication Year'); ax2.set_ylabel('FEV1% Predicted')
ax2.set_title('H2b: Trial FEV1% over Time', fontweight='bold')
ax2.xaxis.set_major_locator(MaxNLocator(integer=True))
fig.tight_layout()
save_figure(fig, "fig8a_h2_age_and_fev1_over_time")

# Diagnostics
fig_d2 = regression_diagnostics_plot(model_h2_age, title_prefix="H2a: ")
save_figure(fig_d2, "fig8b_h2_age_diagnostics")
fig_d2b = regression_diagnostics_plot(model_h2_fev1, title_prefix="H2b: ")
save_figure(fig_d2b, "fig8c_h2_fev1_diagnostics")

# Arm-level sensitivity with cluster-robust SEs
arm_data = arms[['cov_nr', 'age_mean', 'fev1_pct_mean']].dropna(subset=['age_mean'])
arm_data = arm_data.merge(papers[['cov_nr', 'publication_year']], on='cov_nr', how='inner')
arm_data = arm_data.dropna()

model_h2_age_arm = smf.ols('age_mean ~ publication_year', data=arm_data).fit(
    cov_type='cluster', cov_kwds={'groups': arm_data['cov_nr']}
)
beta_age_arm = model_h2_age_arm.params['publication_year']
ci_age_arm = model_h2_age_arm.conf_int().loc['publication_year']
p_age_arm = model_h2_age_arm.pvalues['publication_year']
print(f"\nH2a arm-level (cluster-robust SE):")
print(f"  beta = {beta_age_arm:.3f} [{ci_age_arm[0]:.3f}, {ci_age_arm[1]:.3f}], p = {p_age_arm:.4f}, n_obs = {len(arm_data)}")

arm_data_fev1 = arms[['cov_nr', 'age_mean', 'fev1_pct_mean']].dropna(subset=['fev1_pct_mean'])
arm_data_fev1 = arm_data_fev1.merge(papers[['cov_nr', 'publication_year']], on='cov_nr', how='inner')
arm_data_fev1 = arm_data_fev1.dropna()

model_h2_fev1_arm = smf.ols('fev1_pct_mean ~ publication_year', data=arm_data_fev1).fit(
    cov_type='cluster', cov_kwds={'groups': arm_data_fev1['cov_nr']}
)
beta_fev1_arm = model_h2_fev1_arm.params['publication_year']
ci_fev1_arm = model_h2_fev1_arm.conf_int().loc['publication_year']
p_fev1_arm = model_h2_fev1_arm.pvalues['publication_year']
print(f"\nH2b arm-level (cluster-robust SE):")
print(f"  beta = {beta_fev1_arm:.3f} [{ci_fev1_arm[0]:.3f}, {ci_fev1_arm[1]:.3f}], p = {p_fev1_arm:.4f}, n_obs = {len(arm_data_fev1)}")

