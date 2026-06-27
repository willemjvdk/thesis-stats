## TABLES

# table 1

table_caption: "Table 1 Win ratio analysis of the mAFA-II randomized cluster trial"

table_footnote: "Abbreviations: CI, confidence interval; HR, hazard ratio; IR, incidence rate; IS, ischemic stroke; TE, thromboembolism; WO, win odds; WR, win ratio. a As reported in Guo et al, 2020.7 b Numbers and IR (95%CI) for total number of events occurred during follow-up."

table_body:
<table><tr><td></td><td colspan="2">Number of Events and IR (95% CI) per 100 persons-year</td><td></td><td></td><td></td></tr><tr><td>Outcome</td><td>mAFA (n = 1646)</td><td>Usual Care (n = 1678)</td><td>1/HR (95%CI)a</td><td>WR (95%CI)</td><td>WO (95%CI)</td></tr><tr><td>Composite outcome of death, IS/TE, and rehospitalization</td><td>32 (IR: 2.8 [1.9–3.9])</td><td>101 (IR: 7.9 [6.4–9.6])</td><td>2.56 [1.49–4.55]</td><td>2.78 [1.85–4.17]</td><td>1.06 [1.04–1.08]</td></tr><tr><td>All-cause death†</td><td>12 (IR: 1.0 [0.5–1.8])</td><td>25 (IR: 1.9 [1.2–2.8])</td><td></td><td></td><td></td></tr><tr><td>IS/TE‡</td><td>7 (IR: 0.6 [0.2–1.2])</td><td>6 (IR: 0.5 [0.2–1.0])</td><td></td><td></td><td></td></tr><tr><td>Rehospitalizationb</td><td>20 (IR: 1.7 [1.0–2.7])</td><td>75 (IR: 5.9 [4.6–7.3])</td><td></td><td></td><td></td></tr></table>

## EXTRACTED SECTIONS

# RESULTS
A higher proportion of wins observed in the mAFA intervention group

WR:2.78,95%Cl: 1.85-4.17

Win Odds:1.06,95%Cl:1.04-1.08

mAFA Intervention

Usual care

Number of Wins

Visual summary.Mobilehealth-technologyintegratedcareforAtrial Fibrilation:Awinrationanalysis fromthemAFA-l randomized clinical trial (Created with Biorender.com).

# Methods
Details on the design and primary results of the mAFA-II have been reported elsewhere.7,8 Briefly, the mAFA-II was a cluster randomized trial which enrolled adult patients with AF ( 18 years), between June 1st, 2018 and August 16th, 2019. Clusters were randomized in a 1:1 ratio to the mAFA intervention or usual care, across 40 participating centers in China. The main exclusion criteria were as follows: patients with mechanical prosthetic valve, patients with moderate-to-severe mitral stenosis, and subjects unable to be followed up for 1 year for any reason, or to provide informed consent. The study was approved by the Central Medical Ethic Committee of the Chinese People’s Liberation Army General Hospital and by local institutional review boards. All patients gave a written informed consent at enrolment. The study was conducted in accordance with the Declaration of Helsinki and the Consolidated Standards of Reporting Trials reporting guidelines.

The mAFA intervention consisted of a mHealth-technology-implemented “Atrial Fibrillation Better Care” (ABC) pathway, which is an integrated approach proposed to improve AF management.9 Consistently with the original definition, the ABC pathway, implemented in the mAFA intervention, was defined as follows: “A” criterion: administration of anticoagulant according to the regular and dynamic assessment of thromboembolic and bleeding risks, with dose adjustments according to the regular reassessment of renal and liver function; “B” criterion: periodical assessment of patient-reported symptoms (evaluated according to the European Heart Rhythm Association classification), as well as symptoms-directed management (which included patientcentered and symptom-directed rate or rhythm control treatments); “C” criterion: management optimization of the concurrent conditions and comorbidities (e.g., monitoring of blood pressure monitoring, and consequent management of hypertension), including lifestyle factors.

Subjects allocated to “usual care” were managed according to local practices.

# Outcomes and Follow-up
All patients were followed up for the occurrence of clinical events at 6 months and 1 year after the inclusion. The primary endpoint was the composite outcome of all-cause death, ischemic stroke or systemic thromboembolism, and rehospitalization. Information regarding other secondary outcomes (which included bleeding events [intracranial

and extracranial] and cardiovascular outcomes [recurrent AF, heart failure, acute coronary syndrome]) were also collected during follow-up.

The primary analysis of the trial was conducted according to a time to first event approach, using adjusted Cox-regression models.7 Here, we analyzed the effect of the mAFA intervention on the primary composite outcome according to the WR method, using the unmatched pairs approach. The events composing the primary composite outcome were considered as follows, according to their priority (high to low): (1) allcause death, (2) ischemic stroke or systemic thromboembolism, and (3) rehospitalization.

## Statistical Analysis

For this analysis, we used the unmatched pairs approach described by Finkelstein and Schoenfeld.10 Full details on the calculation of WR3,6 and calculation of 95% CI11 used in this analysis are reported elsewhere. Briefly, each patient in the mAFA intervention was compared with each patient in the usual care group, for the occurrence of the highest-priority event (i.e., all-cause death); for each comparison, the “winner” was determined as the patient who did not have the event or who experienced the event later. If no winner could be declared (e.g., because no event occurred in both patients, etc.), the comparison was then performed for the subsequent outcome in order of priority (i.e., ischemic stroke or thromboembolism), and so on. The number of comparisons “won” by patients in each group was noted, as well as the number of comparisons with “no winner” (ties). The WR was then expressed as the ratio of wins of patients assigned to mAFA intervention on wins of patients assigned to usual care. A WR >1, therefore, indicated a beneficial effect of the mAFA intervention (i.e., the number of comparisons won by the patients allocated in the mAFA intervention outnumbered those won by patients allocated to usual care). We reported WR along with 95% CI; we additionally reported for comparison the 1/HR (95% CI) derived from the adjusted Cox-regression models, as reported in the primary analysis of the mAFA-II trial.7

Given the potential issues in interpreting WR in the presence of a large amount of ties,12 we additionally calculated the win odds (WO), which has been proposed to account for ties, and in which ties are counted as half win and half losses.13,14

All the statistical analyses were conducted using R 4.2.1 (R Foundation for Statistical Computing 2020, Vienna, Austria), using “survival” 15, “WinRatio,” and “WINS” packages.

# Results
Between June 1, 2018 and August 16, 2019, 3,324 patients were enrolled in the trial; 1,646 were allocated to mAFA intervention and 1,678 to usual care. Baseline characteristics and treatments of the cohort and primary results of the trial were reported elsewhere.7 Briefly, over a mean follow-up of 291 days, 133 primary outcomes occurred (32 in mAFA intervention group and 101 in the usual care group), with a total number of 12 deaths, 7 ischemic stroke/systemic thromboembolism, and 20 rehospitalizations among

patients allocated to mAFA intervention, and 25 deaths, 6 ischemic stroke/systemic thromboembolism, and 75 rehospitalizations among patients allocated to usual care.

Results of the WR analysis are summarized in ►Fig. 1 and ►Table 1. There was a total of 2,761,988 unmatched patient pairs in this analysis, with a total of 119,601 (4.3% of the total comparisons) wins for mAFA intervention and 43,032 (1.6%) wins for the usual care group, while the number of comparisons with no winner (ties) was 2,599,355.

The WR analysis showed that patients allocated to mAFA intervention had a lower risk of the primary composite outcome of all-cause death, ischemic stroke or systemic thromboembolism, and rehospitalization (WR: 2.78, 95% CI: 1.85–4.17, p < 0.001), consistent with the original analysis according to the adjusted Cox-regression model7 (1/HR: 2.56, 95% CI: 1.49–4.55).

A beneficial effect of the mAFA intervention was observed also according to WO analysis, although the inclusion of ties substantially mitigated the difference between mAFA intervention and the usual care group (WO: 1.06, 95% CI: 1.04– 1.08, p < 0.001).
