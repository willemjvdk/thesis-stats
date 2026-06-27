## TABLES

# table 1

table_caption: "Table 1. Summary of the human’s body degrees of freedom treated at each game with the type of score collected."

table_footnote: []

table_body:
<table><tr><td>Games</td><td>Joint movements</td><td>Performance score</td></tr><tr><td>Goalkeeper</td><td>Shoulder flexion/extension</td><td>Number of shots blocked - max. of 4</td></tr><tr><td>Clean-the-bathroom</td><td>Shoulder flexion/extension and vertical and horizontal abduction/adduction</td><td>Percentage of accuracy following a trajectory or covering an area of the screen</td></tr><tr><td>Clean-the-horse</td><td>Shoulder flexion/extension and vertical and horizontal abduction/adduction</td><td>Percentage of accuracy following a trajectory</td></tr><tr><td>Kitchen</td><td>Shoulder flexion/extension and vertical and horizontal abduction/adduction Elbow flexion/extension</td><td>Time to complete 6 repetitions or number of repetitions (&lt;6) completed before timeout</td></tr><tr><td>PickApples</td><td>Medio-lateral translation of the pelvis</td><td>Number of apples collected - max. of 9</td></tr><tr><td>Imbalance</td><td>Medio-lateral translation of the pelvis</td><td>Number of coins collected: Level 1 max. 63, level 2 max. 48, level 3 max. 56</td></tr></table>

# table 2

table_caption: "Table 2. Differences in ranges of movement between pairs of evaluations, before and after the treatment with the application, without the application; and the differences between the follow-up evaluation after six months and just after the treatments."

table_footnote: []

table_body:
<table><tr><td>Degree of freedom</td><td>Δ treatment using app</td><td>Δ treatment without using app</td><td>Δ six-month after treatment</td></tr><tr><td>Shoulder flex/ext (°)</td><td>-22.9 ± 37.2</td><td>-3.2 ± 20.5</td><td>25.7 ± 44.6</td></tr><tr><td>Shoulder vertical abd/add (°)</td><td>17.0 ± 42.9</td><td>-3.2 ± 14.1</td><td>14.4 ± 32.1</td></tr><tr><td>Shoulder horizontal abd/add (°)</td><td>1.1 ± 19.5</td><td>-3.8 ± 18.0</td><td>0.8 ± 26.4</td></tr><tr><td>Elbow flexion (°)</td><td>4.1 ± 13.1</td><td>3.2 ± 11.4</td><td>-9.2 ± 21.2</td></tr><tr><td>Waist translation (mm)</td><td>18.4 ± 43.8</td><td>-0.6 ± 30.9</td><td>9.9 ± 40.5</td></tr></table>

# table 3

table_caption: "Table 3. Mean and standard deviation of weekly time spent on using application."

table_footnote: []

table_body:
<table><tr><td>Subject</td><td>Time played per week (hours)</td></tr><tr><td>1</td><td>1.16 ± 0.41</td></tr><tr><td>2</td><td>0.76 ± 0.49</td></tr><tr><td>3</td><td>0.45 ± 0.31</td></tr><tr><td>4</td><td>0.68 ± 0.39</td></tr><tr><td>5</td><td>0.47 ± 0.27</td></tr><tr><td>6</td><td>1.71 ± 0.61</td></tr></table>

# table 4

table_caption: "Table 4. Mean of the subjects’ usability factors outcomes rated from 1 to 5."

table_footnote: []

table_body:
<table><tr><td>Usefulness</td><td>4.1 ± 1.21</td></tr><tr><td>Ease of use and learnability</td><td>4.1 ± 1.21</td></tr><tr><td>Interface quality</td><td>4.2 ± 0.70</td></tr><tr><td>Interaction quality</td><td>4.5 ± 0.58</td></tr><tr><td>Reliability</td><td>3.9 ± 1.46</td></tr><tr><td>Satisfaction and future use</td><td>4.0 ± 1.12</td></tr><tr><td>Overall satisfaction</td><td>4.1 ± 1.14</td></tr></table>

## EXTRACTED SECTIONS

# Methods
## Telerehabilitation system

The basic setup of the system used in this study consists of a depth camera connected to a household computer running our application called Muvity. The Intel Real-SenseTM D415 depth camera (Intel, Santa Clara, CA, USA) was chosen as a relatively low-cost option with good precision. The NuiTrack SDK (3DiVi, Walnut, CA, USA) was used to convert RGB-D data into real-time skeleton tracking without markers. Extraction of joint positions over time permits the user to control an avatar to exercise in a virtual environment. The kinematic information obtained by this means can also be used to compute metrics of the subject’s performance (usually the ROM), as was done for the post-study data analysis. At present, the application offers six games and five exercises. Exercises put the user into a simple environment where they focus on practising a particular movement (single joint motion) by doing a set number of repetitions or as many repetitions as possible within a set timeframe. These movements include flexion and extension of the shoulder (glenohumeral joint), horizontal abduction and adduction of the shoulder, vertical abduction and adduction of the shoulder, flexion of the elbow and medio-lateral translation of the pelvis.

On the other hand, games contain a wide variety of environments designed to resemble ADLs (as this has been shown to be effective in enhancing motor recovery4,27), can incorporate multiple movements and are reinforced with further game mechanics to boost motivation and engagement. These also possess extra internal measures of performance not derived from kinematic data - see Table 1 for a summary of the different degrees of freedom and performance scores associated with each game.

The Goalkeeper game puts the player in a soccer game, where he/she must raise their arms to stop incoming balls. The Clean-the-bathroom game consists in cleaning a fogged mirror by pointing the arm at the screen. The arm must either follow a predefined trajectory to make a pattern on the mirror or be moved all around to clean the entirety of the surface. Clean-the-horse is similar to the previous one. The same arm motions control a hose to wash the dirt off a horse. In this case, the only modality is to follow a predefined trajectory to draw geometrical shapes. The Kitchen game consists of three different scenarios where the player must follow a sequence of movements emulating kitchen activities involved in preparing a pizza, such as chopping ingredients or mixing dough.

PickApples and Imbalance games both deal with the medio-lateral translation of the waist. The swinging

motion of the body (shifting body weight) allows the player to control their avatar to gather collectibles. In the case of PickApples, the avatar is a basket that swerves to catch apples falling from a nearby tree. In the case of Imbalance, the avatar is invisible as the game adopts a first-person perspective. The player is taken through one of three levels, moving forward automatically but with the ability to move from side to side to collect coins and avoid obstacles.

Both in the case of exercises and games, the time-totime positions of joints as reported by the skeleton extraction algorithm are exported to an external database for later processing and analysis. Other statistics of application usage, such as time played are also collected, as are the performance scores reported in Table 1 in the case of games. A physiotherapist can access this data server-side to track the progress of their patients asynchronously.

## Feasibility study

Recruitment was conducted primarily through ADFO’s network. Only subjects who fulfilled all of the following inclusion criteria were eligible for involvement in the trial:

would impair their ability to process and perceive visual stimuli.

Physiotherapists within the association contacted their post-stroke subjects (a total of 16) about the possibility of trying out Muvity application. Of these, ten met all inclusion criteria and were selected for the study (mean and standard deviation of age = 49.7 § 12.3 years, 5.5 § 3.8 years from the stroke, seven women and three men). Participants were then randomly split into two groups by a physiotherapist who did not take part in subsequent evaluations. A cross-over study design was adopted. Both groups followed two eight-week periods of in-home rehabilitation. One of the groups partook in telerehabilitation by means of the provided application, whereas the other conducted conventional rehabilitation. At the end of the first eight-week period, the roles of the groups were exchanged.

The conventional rehabilitation treatment consisted of 30-minute sessions of upper-limb and weight-shifting movements that the subjects were asked to do on their own three days per week. Prior to beginning treatment, subjects had a face-to-face session (»15 minutes) with a physical therapist who instructed them on how to do the exercises and handed them a sheet of paper with a training routine. This setup mirrors the maintenance rehabilitation treatment that most post-stroke subjects who do not regularly frequent private rehabilitation centers get in their chronic stage. Similarly, subjects were also instructed to train for 30 minutes, three times per week for the telerehabilitation treatment. In this case, the training consisted of doing exercises and playing games with the

application. Prior to the beginning of the treatment, a physiotherapist from ADFO visited the subject’s home to set up the telerehabilitation system, either on the subject’s personal computer or on one loaned to them by the association. During these visits, the physiotherapist also instructed them on how to use the application and how to play each of the games (sessions of »15 minutes). Subjects in both groups were given the freedom to train more if they so desired. This permits a soft measurement of the impact of the application on the user’s motivation to continue with their rehabilitation.

The subjects rested for a two-week washing-out period in-between the two in-home rehabilitation phases (prior to the exchanging of roles of the groups). Clinical evaluations of the subjects were conducted before and after each of the rehabilitation phases (for a total of four evaluations). These evaluations were performed by physiotherapists at ADFO’s facilities and consisted of: measuring the degree of disability via the Functional Independence Measure (FIM),32 determining the ability to self-balance via the Berg Balance scale,33 measuring the perceived intensity of pain that the subject was under with a simple Visual Analog Scale (VAS),34 and assessing the self-reported health status of the subject via the SF-36 questionnaire,35 In addition, during these evaluation sessions, the ROM of the anatomical degrees of freedom mentioned in the previous section was captured using the telerehabilitation system to allow comparisons of these metrics across treatment plans. In total, when accounting for this washing-out period, the study lasted for 18 weeks. Six subjects finished the full 18- week plan - see Fig. 1 for a rundown of participant retention throughout the different stages of the study. Those that finished were asked to fill out a satisfaction questionnaire, adapted from Parmanto et al.’s Telehealth Usability Questionnaire (TUQ).36 This questionnaire was designed to evaluate a telehealth implementation and service by covering all the usability factors (i.e., usefulness, ease of use, effectiveness, reliability, and satisfaction). See supplementary material - Satisfaction questionnaire - for a list of the questions included in the version used in this study. Six months after the end of the study, those subjects who finished the entire program were also called back to ADFO for a follow-up evaluation. These follow-ups were conducted in exactly the same manner as the four evaluations done during the study. The Ethics Committee of the Universitat Politecnica de Catalunya reviewed and issued local institutional approval for this study prior to the beginning of the interventions. The participants provided written informed consent.

## Data analysis

Data acquired from the subjects during the in-home treatment were processed and analyzed with MATLAB (Mathworks, Natick, MA, USA) in order to obtain consistent results of the rehabilitation sessions’ performance. All

joint angles and positions were calculated from the joint data recorded by the depth camera. Noise due to bad or incorrect point detections was removed with a median filter. We also calculated the ROM for the right and left sides of the body in the exercises and games, and the performance of the games in terms of scores (e.g. percentage of collected coins, percentage of mirror cleaning or the time that has elapsed until the game goal has been reached, among others). In addition, the time spent on each exercise and game were also extracted from the application.

All these above-mentioned data were calculated for each rehabilitation session and averaged per day and week. The average per week was used to compare ROM, games’ performance and the total time using the application for each subject, whereas the average per day was used to study correlation among all the variables. Correlations among the calculated ROMs per each week were also calculated. Each subject underwent five evaluations in total. We measured the difference between the evaluations after and before the time period with and without application in order to observe if there was an improvement or a difference between the two periods.

Correlations and differences of ROM (parametric variables) within treatment and between treatments were assessed with t-Student tests. Significant differences of FIM, Berg, VAS and PCS scales (non-parametric) within and between treatments were assessed with the Wilcoxon-Mann-Whitney test. In both tests, a significant difference was considered when p-value < 0.05. Effect sizes were calculated using Hedge’s g.37

# Results
## Evaluations

The averages of maximum values for all assessed ROMs and across all participants were superior with the telerehabilitation system treatment compared to the conventional treatment, except for shoulder flexion (Table 2). However, those differences were not statistically significant (p > 0.05). The effect sizes were considered low for the elbow flexion (Hedge’s g = 0.07), and medium for shoulder horizontal abduction (g = 0.25), shoulder vertical abduction (g = 0.61), shoulder flexion (g = 0.63), and waist translation (g = 0.48).

The VAS score (measurement of pain feeling) was the physical outcome, out of the four physical scales assessed, which reported the highest effect size when comparing both treatments. Most subjects reported less pain intensity after using Muvity than with the traditional rehabilitation (Fig. 2), though no statistical significant differences were observed within VAS scores (with g = 0.65). Muvity decreased the pain level in Subjects 2, 3 and 4 up to a difference of 6 points. Subjects 1 and 5 did not have a difference in pain level in any of the two treatments. However, Subject 6 showed higher VAS score differences with Muvity than following traditional rehabilitation. Six months

after the treatment, the level of pain decreased for three subjects and increased for the others. Four of the six subjects maintained or improved their functional independence (FIM score) with the application (Fig. 2). However, the effect size was low ( g = 0 . 1 3 ). The exceptions were Subject 4 (with a difference of 1) and Subject 6, the latter being the same subject that reported the highest pain intensity using the application. Six months after the treatment, the FIM score decreased for four subjects and kept constant for the other two.

After any treatment (in both, with and without application), an increase of the Berg balance outcome was observed on most subjects (Fig. 2). Only Subject 3 showed a decrease without the application, and Subject 4 a decrease using the application. However, the differences in Berg score were superior in five subjects without using the application compared to the treatment using the application (with an effect size of g = 0.25, no statistical difference). After six months, the Berg scores increased for

three subjects and decreased for the other three. PCS score decreased in five and three subjects using the application and without using it, respectively (Fig. 2). In two subjects the difference was superior using the application (with g \ = \ 0 . 3 2 ,, no statistical significant difference). After six months, PCS score increased for five subjects.

## Monitored data

The total time that the subjects spent using Muvity during the treatment is shown in Table 3. This is the time within the exercises and games, without counting the time spent on the menus or intermediate resting periods. During the eight weeks period without the application, the subjects were required to write down the time spent following the exercises and all six subjects mentioned that they followed three 30-min sessions per week.

Significant positive correlations among all five analyzed ROM variables during the eight weeks monitored with

the application (Figs. S1 to S6, Supplementary Material) were observed (p < 0.01), except for the pair of vertical shoulder abduction and waist translation. Three pairs had r > 0.8 (shoulder flexion / vertical shoulder abduction, shoulder flexion / elbow flexion, vertical shoulder abduction / elbow flexion). The other pairs had r > 0.25.

The results also show that we could identify progressions, abnormalities or status of the subjects remotely. For instance, Subject 5 had the left side impaired; therefore, the maximum shoulder flexion angle that we observed in this case was very low (overall < 10°). The same subject tended to support the weight more in the right side (nonparetic leg) than on the left, as illustrated in Fig. S5 showing the medio-lateral translations of the waist (split between right and left) during the Swing exercise (consisting of repetitions of waist’s medio-lateral translations without moving the feet). For this subject, almost no difference can be observed between the physical evaluations before and after the period without application.

The increase of the ROM is also reflected in the performance of the games. For instance, the Goalkeeper game deals with shoulder flexion at different levels, according to the height of the ball. The application records the ROM, but also the score, as shown in the example of Fig. 3 for

Subject 6, who improved the performance in this game over the weeks. However, we could not analyze all data of the games for all weeks since the participants did not consistently play all games.

## Satisfaction

All main items evaluated within the satisfaction questionnaire were higher or equal than 3.9 points over 5.0 and a standard deviation inferior to 1.5 points (Table 4). All detailed results of the TUQ are shown in Table S1. Some questions should be highlighted as being of great value for the objectives of the study. These questions relate directly to the benefit of the application during the rehabilitation program (questions 6, 12, 13 and 16 from Table S1, Supplementary Material). All these questions ranged above 3.6 over 5.0 (72%) of satisfaction, highlighting that the system is a good tool for the physiotherapy sessions and the application increased the subjects’ motivation during the rehabilitation.

Moreover, the satisfaction questionnaire included some questions related to the interface satisfaction. The exercises and all the game environments were scored above 3.29, resulting in 3.92 § 1.24 points (78.4%). The two games with the highest score were PickApples and Imbalance, whose main aim was to promote the weight-shifting exercise. PickApples was the game that subjects liked the most with a score of 4.43 § 0.79 over 5.00. Clean-the-horse was the game less attractive for the subjects, although its score was around 3.29 1.5.

# Supplementary materials
Supplementary material associated with this article can be found in the online version at doi:10.1016/j.jstrokecere brovasdis.2022.106791.
