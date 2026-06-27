## TABLES

# table 1

table_caption: "Table 1 Description of participants"

table_footnote: []

table_body:
<table><tr><td></td><td>Total</td><td>Chatbot</td><td>Paper</td></tr><tr><td>Group: Participants</td><td>112</td><td>55</td><td>57</td></tr><tr><td>Sex:</td><td></td><td></td><td></td></tr><tr><td>Men</td><td>65</td><td>32</td><td>33</td></tr><tr><td>Women</td><td>47</td><td>23</td><td>24</td></tr><tr><td>Employment situation:</td><td></td><td></td><td></td></tr><tr><td>Active</td><td>82</td><td>44</td><td>38</td></tr><tr><td>Disabled</td><td>4</td><td>2</td><td>2</td></tr><tr><td>Retired</td><td>20</td><td>6</td><td>14</td></tr><tr><td>Unemployed</td><td>6</td><td>3</td><td>3</td></tr><tr><td>Educational level:</td><td></td><td></td><td></td></tr><tr><td>Basic studies</td><td>28</td><td>9</td><td>19</td></tr><tr><td>Medium studies</td><td>25</td><td>13</td><td>12</td></tr><tr><td>Vocational Training</td><td>35</td><td>17</td><td>18</td></tr><tr><td>University graduates</td><td>14</td><td>8</td><td>6</td></tr><tr><td>Not specified</td><td>10</td><td>8</td><td>2</td></tr><tr><td>Diagnosis:</td><td></td><td></td><td></td></tr><tr><td>Primary HTN</td><td>45</td><td>23</td><td>22</td></tr><tr><td>Secondary HTN</td><td>54</td><td>28</td><td>26</td></tr><tr><td>HTN suspicion</td><td>13</td><td>4</td><td>9</td></tr><tr><td>Diabetes Mellitus:</td><td></td><td></td><td></td></tr><tr><td>No</td><td>94</td><td>47</td><td>47</td></tr><tr><td>Yes</td><td>17</td><td>8</td><td>9</td></tr><tr><td>NA</td><td>1</td><td></td><td>1</td></tr><tr><td>Cardiovascular disease:</td><td></td><td></td><td></td></tr><tr><td>No</td><td>103</td><td>49</td><td>54</td></tr><tr><td>Yes</td><td>9</td><td>6</td><td>3</td></tr><tr><td>Chronic Kidney Disease:</td><td></td><td></td><td></td></tr><tr><td>No</td><td>57</td><td>30</td><td>27</td></tr><tr><td>Yes</td><td>54</td><td>25</td><td>29</td></tr><tr><td>NA</td><td>1</td><td></td><td>1</td></tr><tr><td>Age:</td><td></td><td></td><td></td></tr><tr><td>Min.</td><td>21.0</td><td>21.0</td><td>31.0</td></tr><tr><td>1st Qu.</td><td>42.8</td><td>40.0</td><td>45.0</td></tr><tr><td>Median</td><td>52.0</td><td>49.0</td><td>55.0</td></tr><tr><td>Mean</td><td>52.1</td><td>50.2</td><td>53.9</td></tr><tr><td>3rd Qu.</td><td>61.3</td><td>58.0</td><td>63.0</td></tr><tr><td>Max.</td><td>87.0</td><td>87.0</td><td>80.0</td></tr></table>

# table 2

table_caption: "Table 2 List and description of available commands in TensioBot. Some of them are only available for the doctor or nurse"

table_footnote: []

table_body:
<table><tr><td>Command</td><td>Description</td><td>Role</td></tr><tr><td>/check</td><td>Main command, used for starting the procedure of blood pressure measuring</td><td>Patient</td></tr><tr><td>/appt</td><td>Allows to change the date and hour of the medical appointment or to cancel it</td><td>Patient</td></tr><tr><td>/graph</td><td>Shows a line chart of historical BP measurements</td><td>Patient</td></tr><tr><td>/change</td><td>Schedule alerts or cancel any of the two daily alerts or both</td><td>Patient</td></tr><tr><td>/video</td><td>Shows a short video about how to correctly measure BP at home</td><td>Patient</td></tr><tr><td>/cancel</td><td>Cancel any ongoing command</td><td>Patient</td></tr><tr><td>/patients</td><td>Shows a list of all the patients (UserID, username, date created, appointment date) and downloads an XLS file with all that data</td><td>Doctor / Nurse</td></tr><tr><td>/query</td><td>TakesUserID as argument and shows username, date created and appointment date of an specificUserID, and downloads an XLS file with data: dates, time, systolic and diastolic BP in mmHg.</td><td>Doctor / Nurse</td></tr></table>

# table 3

table_caption: "Table 3 Two sample t-test and Wilcoxon test values (measuring difference of the means between BP, systolic and diastolic, in Holter-Control vs Holter-Bot)"

table_footnote: []

table_body:
<table><tr><td>BP</td><td>t</td><td>df</td><td>p value</td><td>95% Conf. Int.</td><td>mean intervention</td><td>mean control</td><td>Wilcoxon test (p value)</td></tr><tr><td>Systolic</td><td>0.956</td><td>73</td><td>0.342</td><td>(-2.343, 6.667)</td><td>-0.338</td><td>-2.500</td><td>0.3886</td></tr><tr><td>Diastolic</td><td>0.130</td><td>73</td><td>0.897</td><td>(-2.856, 3.253)</td><td>-1.879</td><td>-2.078</td><td>0.6898</td></tr></table>

## EXTRACTED SECTIONS

# Methods
## Overview

A 2-arm, randomized, controlled trial of an intervention based on the TensioBot mobile application was carried out over 2 years (2018–2020). This clinical trial has been approved by the Clinical Research Ethics Committee of the BioAraba Health Research Institute, with approval number/ ID 2017–031 and PI LE.

## Subjects and recruitment

We recruited 112 patients that needed to check their BP daily, twice, 7 days before the medical appointment. Half of them were randomly assigned to the bot intervention group and the other to the control group. Near 48% of all the patients had some kind of chronic kidney disease. Table 1 summarizes the characteristics of participants.

## Inclusion criteria

## Exclusion criteria

Patients were excluded on the basis of these criteria:

& Previous diagnosis of severe psychiatric disorder.

## TensioBot intervention description

Patients in the intervention group were asked to contact a chatbot called TensioBot on Telegram. We will start

describing Telegram and then define the TensioBot commands. Figure 1 shows some screenshots of a session with TensioBot.

## Telegram platform

Telegram is a popular IM application -more than 500 million active users-. In 2014, Telegram was the first IM provider to introduce the ability to develop and interact with chatbots. Chatbots can respond to text or voice commands from the user, display links, images or videos. Users can start a conversation with a bot by searching for its name as if it were a human contact in their contact list. Users can also click on a direct link to automatically open a conversation with a specific bot.

## How TensioBot works

One week before the doctor’s appointment, TensioBot asks patients to measure their BP twice a day, usually once in the morning and once in the evening (the alert times can be edited at any time). When the user receives the alert, he/she should proceed to use the tensiometer and write down on a

paper the BP values (highest, lowest) answering the questions posed by the chatbot. It then informs patients to wait two minutes and proceed again for a second measurement. After the second set of measurements, TensioBot shows a line chart with the entire BP history. If after the two-minute waiting period the patient enters a BP value higher than 5 mmHg compared to the values of the first measurement, the bot prompts the patient to perform a third measurement 2 min later.

If a patient enters a BP value that is outside normal levels, the bot asks for confirmation. If it was a typing error by the user, it asks the patient to check the measurement again, and if the number was indeed correctly introduced, the bot notifies the doctor. All the pressure-numbers checked during the last seven days are reflected in a line chart that shows the evolution of the data (third picture in Fig. 1).

TensioBot also offers an option to display a helpful video on good BP measurement practices showing tips on how and when to take it, how to adjust the tensiometer, how to adjust the body position, etc. Once a day the bot also sends a message with other tips related to good BP measurement practices. Finally, the bot offers a command to remind the patient of the scheduled time for the next medical appointment, allowing the

patient to change or cancel it directly through a conversation with the chatbot.

## Administration commands

All of the above functions are available to any regular user (patients), but TensioBot also aims to help the physician with the management of those patients by offering a couple of administration commands, one for downloading a calc sheet with all the blood pressures for each patient and day and another for showing just the data for a specific patient (passed as argument to the command). Table 2 summarizes all the available commands.

## Protocol

Each control patient attending their first medical appointment receives a written procedure on how to self-monitor their BP. The nurse assesses the patients’ knowledge and skills on BP self-monitoring using a checklist and ensures that the patient knows when their next medical appointment is and when to perform BP measurements with a Holter device. For patients in the intervention group, the procedure is quite similar, except that they do not receive the information document on the procedure. In this case, the nurse also helps the user to download and install the Telegram app, if the patient does not already have it installed, and start using TensioBot, registering the user with the bot.

At the second visit, patients in both groups (control and intervention) undergo a knowledge and skills check of the BP self-monitoring procedure. We compare the results between the groups. Besides, we statistically analyze patient adherence with regard to the number of correct BP checks in both groups and the results of a survey administered to the intervention group after the second medical visit.

# Results
## Knowledge and skills about BP checking

We obtained 88 cases for patients who completed both visits. Of these, we eliminated two cases that had a 100% checklist score during their first visit (and therefore their scores could not improve at the second visit).

We wanted to analyze the results of the checklist in relation to patients’ knowledge and skills regarding home BP measurement technique. For each question answered, we gave a score of 1 for those answered correctly and a score of 0 for those answered incorrectly. We summed all the questions and divided by the maximum value, expressing the final value as a percentage.

Then we obtained two columns, one representing the knowledge gain for each set of control patients and a similar one for the set of intervention patients. We wanted to know if the differences in knowledge gains between the two groups were significant, so we applied a t-test, obtaining a t = 2.1159, df = 82.34, p value = 0.03737, 95% confidence interval (0.3915, 12.679) and mean in the Bot group = 24.126, mean in the control group = 17.591.

The p value associated with the test is 0.0374, so we can reject the null hypothesis ( 0) of no difference between the (true) mean, suggesting that the difference in acquired knowledge of both groups is significant (favouring patients from the bot group). We used a non-parametric test, Wilcoxon rank sum test, to compare the ranks between Bot and Paper groups and the difference was also significant, W = 1159.5, p value = 0.04031.

## Effectiveness of TensioBot with regard to the BP checking in-site

In the second visit, a nurse helped each patient to put on a Holter device (ABPM) to check BP during 24 h, and we

discarded measurements during sleep to calculate the daytime means of systolic and diastolic BP (it is well known that BP values are lower during sleep). Considering the Holter values as the gold standard, we contrasted them with the BP checking values of the control and intervention groups (mean difference, for systolic and diastolic values).

We applied a two-sample t-test to the difference of the means between BP (systolic and diastolic values) in Holter-Control vs Holter-Bot, yielding values of Table 3. There was a smaller difference for the TensioBot group, both in systolic and diastolic values, but not significant (Fig. 2). The difference and scattering of values can be better seen on Figs. 3 and 4.

# Results of the satisfaction survey administered to TensioBot users
There were 4 questions in the survey, answered by n = 40 patients from the intervention group: 1) “Do you think that TensioBot is easy to use?”; 2) “Do you think that TensioBot is useful to help you better record your blood pressure values at home?”; 3) “How do you prefer to register your BP?” and 4) “Have you stopped using TensioBot?”

1) Do you think that TensioBot is easy to use?

92.5% of those surveyed patients think it is quite easy or very easy to use. Yet, there are 3 patients who think it is quite difficult

Very easy n = 23, Pretty easy n = 14, Quite difficult n = 3.

2) Do you think that TensioBot is useful to help you better record your BP values at home?

72.5% of respondents think it is very useful to use / all respondents think it is quite useful or very useful

Very useful n = 29. Quite useful n = 11.

3) How do you prefer to register your BP?

92.5% indicate that they prefer to register their BP at home using TensioBot instead of doing the registration on paper

Prefer to use the bot n = 37.

Prefer to write the numbers down on a paper n = 3 (despite the fact that some of these 3 people answered that the bot is useful and easy to use).

4) Have you stopped using TensioBot?

Only 6 people (15%) stopped using TensioBot. The main reason patients give is that they have difficulties in using a mobile phone.
