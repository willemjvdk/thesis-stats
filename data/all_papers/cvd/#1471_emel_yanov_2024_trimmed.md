## TABLES

# table 1

table_caption: "Baseline Characteristics of the Two Groups"

table_footnote: "1 Body mass index, 2 New York Heart Association, 3 left ventricular fractional output, 4 ischemic heart disease"

table_body:
<table><tr><td></td><td>Total subjects, n = 36</td><td>mHealth group, n = 25</td><td>Standard observation, n = 11</td><td>p</td></tr><tr><td>Age, years</td><td>60.3 ± 12</td><td>61</td><td>64.5 ± 10.6</td><td>0.23</td></tr><tr><td>Men, n (%)</td><td>27 (75)</td><td>20 (83.3)</td><td>7 (63.6)</td><td>0.3</td></tr><tr><td>BMI1, kg/m2</td><td>29.62 ± 6.9</td><td>27.6 ± 5.8</td><td>33.7 ± 7.5</td><td>0.016</td></tr><tr><td>NYHA CHF class2:</td><td>-</td><td>-</td><td>-</td><td>0.39</td></tr><tr><td>I-II, n (%)</td><td>19 (52.8)</td><td>12 (48)</td><td>7 (63.6)</td><td>-</td></tr><tr><td>III-IV, n (%)</td><td>17 (47.2)</td><td>13 (52)</td><td>4 (36.4)</td><td>-</td></tr><tr><td>LV FO, %</td><td>50.7 ± 9.2</td><td>48.7 ± 7.6</td><td>54.9 ± 11.3</td><td>0.1</td></tr><tr><td>IHD4, n (%)</td><td>23 (63.9)</td><td>15 (60)</td><td>8 (72.7)</td><td>0.46</td></tr></table>

## EXTRACTED SECTIONS

# Materials and methods
## Study design

A two-stage randomized controlled trial on the effects of telemonitoring using a mobile platform for outpatients with chronic heart failure was conducted.

Patients were included in the study if they were over 18 years of age, had no signs of decompensation, and had a smartphone with internet access. Patients were included within seven days of hospitalization due to decompensated heart failure. Diagnoses of chronic heart failure (CHF) were established in accordance with the clinical guidelines for the diagnosis and treatment of chronic heart failure of the Russian Society of Cardiology [7]. Non-inclusion criteria were the inability to install the app on a smartphone, pregnancy, and alcohol or drug abuse. Exclusion criteria included inability to use the app due to functional or visual impairments observed during the study and unwillingness to take part in the study. The study was approved by the Ethics Committee of Sechenov University and complied with the criteria of the Declaration of Helsinki. Each participant provided signed voluntary informed consent.

Baseline demographic characteristics, clinical data, and quality of life scores based on the Minnesota Living with Heart Failure Questionnaire (MLHFQ) were collected at enrolment. The MLHFQ is a well-known self-administered questionnaire, one of the most widely used for assessment of quality of life in patients with heart failure. It consists of 21 items, each scored on a scale ranging from 0 (not at all) to 5 (very much), assessing physical and emotional parameters. The total score ranges from 0 to 105, with 0 indicating the best quality of life and 105 the worst [8].

All patients were randomized into two groups: group 1 used the mHealth app and group 2 received standard care. A follow-up call was scheduled after the three-month follow-up period for both groups.

## mHealth remote monitoring platform

As part of this study, an experimental patient monitoring platform was developed. The platform consists of a server and interfaces for patients and medical professionals performing remote monitoring.

The server consists of a relational database (PostgreSQL) and visual programming tool Node-RED. Both apps run in Docker containers and are managed using Docker Compose. The web interface, developed using the Vue.JS framework, connects to the backend through an application pro-

gramming interface (API) and allows healthcare professionals to track patient activity in real time. The web interface, together with the server, are hosted on a virtual server located in Russia.

Patients access the platform using the free mobile messaging app Telegram Messenger, which is available for both Apple and Android operating systems. The platform interface is essentially a chatbot which sends a questionnaire at a specific time and allows patients to select one or more predefined answers. Processing of chatbot commands is managed by Node-RED and patient responses are stored in PostgreSQL (Fig. 1).

## mHealth platform remote monitoring group

The messaging app was installed on patients’ smartphones prior to the study. All patients were instructed and trained to use the app. Patients received a questionnaire every day at 12 noon. On Mondays this consisted of seven control questions and from Tuesday to Sunday it consisted of six questions. Patients could start, pause, and continue responding for 24 h before the next questionnaire was available. For security reasons, patients’ personal data were not entered or stored in the program. All responses received were stored in a PostgreSQL database and a web interface was used to monitor the status of patients and their responses.

The questionnaire was based on the CHF clinical assessment scale (CCAS) [7]. This was designed specifically for use within the mHealth platform to assess symptoms and identify signs of decompensation of HF. Response options for each question were assigned one of three flags: green (good), yellow (warning), and red (alarm). The combined result (or patient flag) was determined by assigning a color reflecting the overall condition of the patient. If all answers were marked green, then the result was green. If at least one answer was marked yellow, then the overall result was yellow. Finally, if at least one answer was marked red, the overall result was red. The web interface was regularly checked by the research physician and, if a red flag was detected, the physician contacted the patient by telephone to decide needs regarding adjustments to therapy, consultation, or hospitalization.

Patients measured their blood pressure and heart rate and assessed the presence and severity of edema every morning. They also had to weigh themselves at least once a week. These indicators were sent with questionnaire responses (Fig. 2).

## Endpoints

The primary endpoint was decompensation of HF (hospitalization for CHF or all-cause death or parenteral loop diuretic use) over three months. The secondary endpoint

was change in quality of life as measured by the MLHFQ at baseline and three months after study entry. Another secondary endpoint was compliance with follow-up, measured as the number of patients completing the questionnaire at least once per week over the three-month period.

## Statistical analysis

Categorial variables are presented as frequencies and percentages and numerical variables as means and standard deviations for normally distributed data and medians and interquartile ranges for non-normally distributed data. Differences were taken as significant at p < 0.05. All analyses were run in Statistica (Data Analysis Software) version 12.

# Results
The study included 64 patients with HF; 25 patients in the remote monitoring group and 11 in the standard monitoring group completed the three-month follow-up period. There were more men in the mHealth group than the standard care group, as well as a significantly lower mean body mass index in the mHealth group. Cardiac contractility (LVEF) was comparable (Table 1). There was no between-group

difference in quality of life at baseline (34.4 ± 17.8 vs. 44; p = 0.65) or at three months (25.2 ± 14.3 vs. 38.8 ± 23.9; p = 0.25). However, within-group assessment over the three months demonstrated a significant improvement in the quality of life in the remote observation group (34.4 ± 17.8 versus 25.2 ± 14.3; p = 0.048) with no change in the reference group (44 versus 38.8 ±23.9; p= 0.25). Compliance with remote monitoring was confirmed in 20 patients (80%). The primary end point (decompensation of CHF) was reached in two patients (18%) in the standard observation group and none in the study group (p= 0.028). Two independent episodes of deterioration, based on questionnaire responses, led to changes in diuretic therapy and probably prevented hospitalization (Fig. 3).
