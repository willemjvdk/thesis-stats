## Methods

### Overview

The extraction pipeline is a software system that reads clinical trial papers and uses a large language model (LLM) to pull out structured data—things like how many patients were in each treatment arm, their average age, what percentage were female, their baseline lab values, and so on. The system processes papers for three diseases: COPD (65 papers), cardiovascular disease (412 papers), and diabetes (275 papers). Each paper arrives as a plain-text markdown file, and the goal is to convert it into a structured spreadsheet row where every number has been extracted, checked for internal consistency, and flagged for review if anything looks off.

### Paper Format

The papers are stripped-down versions of published clinical trials. They have been converted from PDF to text (minerU). Each filename starts with a hash symbol followed by a four-digit identifier, the lead author's surname, the publication year, and a "trimmed" label—for example, `#0464_bentley_2014_trimmed.md`. The four-digit identifier (e.g., 0464) serves as the paper's permanent ID throughout the entire pipeline.

### The Two-Pass Extraction Strategy

The system processes each paper twice, in what is called a two-pass architecture. This was designed because early single-pass attempts often produced the wrong number of treatment arms—the LLM would sometimes miss arms or fabricate extras.

**Pass 1 (Arms Extraction).** The first pass uses a very short prompt, only 16 lines long, that asks the model one thing: "How many treatment arms does this study have, and what are they called?" The model returns a tiny JSON object like this: `{"cov_nr": "0464", "n_arms": 2, "arm_labels": ["control (usual care)", "treatment (telemonitoring)"]}`. This step is fast and cheap because the prompt is small and the answer is tiny.

**Pass 2 (Full Extraction).** The second pass uses the main extraction prompt, which is around 1,000 lines long and defines roughly 85 fields that need to be extracted from each arm. The arm count from Pass 1 is saved alongside the Pass 2 results, so later the validator can check whether the extraction actually produced the expected number of arms.

Why two passes? The arms pass is simple enough that it almost never fails. By establishing the arm count upfront, the system gives the full extraction pass a target to aim for and gives the validator a reference to check against. It's a bit like having a spotter when you're counting something complicated—you agree on the big number first, then fill in the details.

### Prompt Design

The main extraction prompt is a long document written in plain English that tells the model exactly what to look for and how to format it. It contains several important rules that shape how the model behaves:

**The Recompute Rule.** When a paper reports both raw counts (e.g., 45 out of 200 patients were smokers) and a percentage (22.5%), the model must recompute the percentage from the raw numbers rather than copying the percentage from the paper. This catches rounding errors and inconsistencies in the source material. If the recomputed percentage differs from what the paper states by more than one percentage point, the model must flag it.

**The Do Not Invent Rule.** The model is explicitly told not to fill in gaps by guessing. If the paper does not report the number of non-smokers, the model must leave that field as missing rather than calculating it by subtraction. Similarly, if a percentage is reported without a raw count, the model must not back-calculate the count—it records only what the paper actually says.

**The N-and-Percent Format Rule.** Fields that represent counts and percentages (such as the number of female participants) must be written as a string in the format `"N (%)"`—for example, `"45 (22.5%)"`. There are separate suffixes for cases where only a count or only a percentage is available. This consistent formatting makes it possible for the validator to later parse these strings and check the arithmetic.

**The Flag-and-Explanation Pairing Rule.** Every "needs discussion" field (like `needs_discussion_gender`, which indicates the gender data has something unusual about it) comes as a pair: a true-or-false flag and an explanation. When the flag is false, the explanation must say "NA". When the flag is true, the explanation must contain actual text describing the issue. Both fields must always be present, even if the flag is false. This prevents the model from silently dropping fields it considers irrelevant.

**Array Fields.** Some fields—like smoking status, which breaks a population into categories such as smokers, former smokers, and non-smokers—are stored as lists (arrays). Each category is a separate entry in the list, formatted as `"Category: Value"`. If the paper does not report a breakdown, the list contains a single entry, `"NA"`.

Each disease has its own prompt version because the clinical fields differ. COPD papers have fields about lung function (FEV1 percentage), diabetes papers have fields about blood sugar control (HbA1c), and cardiovascular papers have fields about heart failure classification (NYHA class). But the core extraction rules—recompute, do not invent, N-and-percent format, flag-and-explanation pairing—are the same across all three diseases.

The prompts are versioned (e.g., `prompt_copd_v11.md` means version 11 of the COPD prompt). When the pipeline runs, it automatically finds the highest-numbered version for the chosen disease. You can also pin a specific version if you want to reproduce an earlier run.

### Calling the Language Model

The pipeline communicates with the LLM through an application programming interface (API)—essentially, the pipeline sends text (the prompt plus the paper) to a remote server, and the server sends back the model's response. The model is instructed to return only valid JSON and nothing else—no explanations, no markdown formatting, just the data.

A critical setting is **temperature**, which controls how random or creative the model's output is. Temperature is locked at zero, meaning the model should always give the same answer to the same question. A runtime assertion in the code prevents anyone from accidentally changing this to a higher value.

API calls sometimes fail—servers get overloaded, connections time out. The pipeline retries failed calls up to three times, waiting one second, then two seconds, then four seconds between attempts. If all retries fail, the paper is marked as an error and may be reprocessed in a later rerun.

For speed, the pipeline can process multiple papers at the same time using parallel workers—essentially, separate processing lanes that run independently. When running in parallel, the delay between API calls is reduced proportionally (if 8 workers share the work, each waits only an eighth of a second between its own calls), but the total rate of calls to the API stays roughly the same. The maximum number of parallel workers is 16.

### Output and Metadata

Every extraction produces a JSON file saved in a versioned output directory, such as `output/results/copd_v11/0464.json`. This file contains a list of arm objects, one per treatment arm, with all the extracted fields. But it also contains something crucial: a `_metadata` section attached to every arm, recording:

- Which prompt version was used (e.g., v11)
- Which model was used (e.g., ds-flash)
- The extraction timestamp (ISO-8601 format)
- The study information from Pass 1 (how many arms were expected and what they were called)

This metadata is what makes the two-pass system work—the validator later reads the Pass 1 arm count from the metadata and compares it to the number of arms actually extracted in Pass 2.

After all papers are processed, the system aggregates all the JSON files into a single CSV spreadsheet (one row per arm, one column per field) for downstream analysis.

### Validation

Once extraction is complete, a separate validation system checks every paper for errors and inconsistencies. The validator operates in five layers, moving from simple structural checks to complex cross-arm comparisons.

**Layer 1: Structural Checks.** The validator first confirms that the JSON is valid and properly formed. It checks that the paper ID inside the file matches the filename. It checks that every required field (all ~85 of them) is actually present, and that no unexpected fields have appeared (the LLM sometimes invents field names). It also checks that arm labels follow the expected naming convention (`control` for the control group, `treat1`, `treat2`, etc., for treatment groups).

**Layer 2: Type and Range Checks.** Each field has a defined type—a number, a true/false flag, a list, or a string from a controlled vocabulary. The validator checks that every field matches its type. Numeric fields are checked against reasonable ranges (age must be between 18 and 120, counts must be at least 1). Fields that are supposed to be integers are flagged if they contain decimals. Fields whose values should come from a fixed set (like healthcare setting, which must be 1, 2, or 3) are checked against that set.

**Layer 3: Intra-Arm Consistency.** Within a single arm, the validator checks that numbers add up. The female count plus the male count should equal the total arm size. The reported percentage of females should match the percentage calculated from the raw counts (within a 1% tolerance). The intervention duration plus the follow-up duration should approximately equal the total study duration. For array fields like smoking status, the validator parses out the count for each category and checks that the sum matches the arm size. If the sum is too low, the auto-fix system can infer a missing category (e.g., "non-smoking (inferred): 85"). If the sum is too high, the finding is flagged for manual review because the error could be in any of the categories.

**Layer 4: Cross-Arm Consistency.** The validator checks that certain values are identical across all arms of the same study. The total study duration (`time_total_days`) must be the same for every arm—a study cannot last 12 weeks for the treatment group and 6 weeks for the control group. It also checks that at least one control arm and at least one treatment arm exist (a paper with only treatment arms suggests a missed extraction).

**Layer 5: Context-Sensitive Checks.** These are disease-specific checks that require domain knowledge. For example, in diabetes papers, the HbA1c severity classification (mild, moderate, or severe) is checked against the numeric mean HbA1c value. If the paper reports mild severity but the mean HbA1c is above 9%, something is inconsistent. For all diseases, severity prefixes in the `disease_severity_other` field are checked against a controlled vocabulary of known medical terms—for COPD, for instance, about 120 terms related to lung disease severity are recognized.

### Findings and the Review Database

Every issue found by the validator is recorded as a "finding." Each finding has a severity level: ERROR for problems that make the data unreliable (like missing required fields or arm count mismatches) and WARNING for issues that should be reviewed but may not affect usability (like a slight arithmetic discrepancy). Findings are stored in an SQLite database (`output/review.sqlite`) that serves as both a record and a review workspace.

The database tracks the full lifecycle of each finding: when it was created, what paper and arm it relates to, its severity and category, the human-readable message describing the problem, whether it can be fixed automatically, its review status (open, accepted, rejected, or fixed), who reviewed it, the resolution rationale, and when it was resolved.

An important feature of the database is its sync mechanism. When the validator runs again—for example, after an auto-fix or after prompt improvements—it does not blindly re-insert all findings. Instead, it deduplicates: if a finding with the same paper, category, and message already exists, it is skipped. If a previous run produced a finding that the new run does not reproduce (meaning the issue has been resolved), that stale finding is automatically removed—but only if it is still in "open" status. Findings that have been manually accepted or rejected are never automatically deleted. This means the database preserves the history of human decisions while automatically cleaning up machine-generated noise.

### Auto-Fix

Some validation issues can be corrected automatically. When the `--fix` flag is used, the validator modifies the JSON files in place to resolve specific types of problems:

- If a severity prefix has the wrong capitalisation (e.g., "copd" instead of "COPD"), it is corrected.
- If an array sum is too low, a "missing (inferred)" category is added with the remaining count.
- If an array sum is too high for smoking status, a warning is written into a separate notes field rather than modifying the reader's extraction.
- If a field is the wrong type (e.g., a decimal where an integer is expected), the value is rounded.
- If the HbA1c severity classification does not match the numeric mean, it is recalculated.

There is also a separate field-transform fix that runs regardless of findings. This corrects common LLM mistakes: renaming hallucinated field names to the correct schema names, removing fields the LLM invented that are not part of the schema, and moving orphaned values into their proper locations. Before any file is modified, a backup copy (with a `.bak` extension) is created, so no change is irreversible.

### Auto-Rerun

The extraction pipeline is designed to detect its own failures and retry. When a run finishes, the system counts errors: papers where only one arm was extracted (suggesting the control group was missed), papers where the JSON could not be parsed, papers that produced no output at all, and papers flagged as "catastrophic" (five or more required fields missing, as determined by the validator). If any errors exist, the pipeline deletes the faulty outputs, renames the originals to `.bak` for forensic inspection, and reruns the extraction—up to a configurable number of times, with a default of three total attempts (one initial run plus two reruns). If zero errors are found after any attempt, the rerun loop stops early.

### Review Workflow

For issues that cannot be fixed automatically, the system provides an interactive review interface. A reviewer can run the validator in review mode for a specific paper, and the system will present each open finding one by one, asking the reviewer to accept it (the extraction is correct and the validator was wrong), reject it (the extraction is wrong but the issue is noted), or mark it as fixed with a corrected value. The reviewer's decision, rationale, and timestamp are recorded in the database.

For batch review across many papers, findings can be exported to a CSV spreadsheet, reviewed in Excel or Google Sheets by adding a decision column (accept or reject) and a notes column, and then re-imported using a batch review script. Alternatively, the SQLite database itself can be opened in a tool like Beekeeper, which provides a spreadsheet-like interface for editing the status and resolution columns directly.

### Reproducibility

Several features ensure that the entire process can be reproduced and audited.

Every LLM call uses temperature zero, meaning the model's output is deterministic—given the same prompt and the same paper, it should always produce the same extraction. This temperature setting is enforced by a runtime assertion that will crash the program if it is changed, making it impossible to accidentally introduce randomness.

Every extraction is tagged with metadata: which prompt version produced it, which model was used, and when the extraction ran. This means any result can be traced back to its exact origin. If the prompt changes between runs, the system can detect this: the version-drift checker compares the prompt version stored in existing outputs against the current prompt version and refuses to run if they differ, preventing the mixing of data extracted under different rules.

Independent comparison runs—for example, testing a new prompt version against an old one, or comparing two different models—can be performed safely using the label system. The `--label` flag appends a suffix to the output directory (e.g., `copd_v11_rerun1`), creating a separate directory that does not overwrite previous results. This allows side-by-side comparisons without duplicating the entire codebase.

Paper sampling for test runs is deterministic: the `--seed` flag fixes the random order, so the same 10 papers are selected every time for a given seed value.

The pipeline produces two types of log files for every run. A verbose log records every step with ISO-8601 timestamps—each paper's start and end, API call details, retries, and errors. A summary file provides a human-readable overview: total duration, papers processed, success and error counts, parallel worker count, model used, token usage, and total API cost (in US dollars). These files are timestamped and never overwritten, creating a permanent record of every extraction run.

The validator produces its own timestamped report (`validation_report.json`) aggregating all findings, and the review database preserves the full history of every finding's creation, review, and resolution. Backup files (`.bak`) are created before any automatic modification, and faulty extractions from reruns are preserved with `.bak` extensions rather than deleted, so the original erroneous output can always be examined.

Taken together, these mechanisms mean that every number in the final dataset can be traced back through an unbroken chain: the extracted value, the model and prompt that produced it, the validation checks that examined it, any corrections that were applied, and the human reviewer who signed off on any remaining issues.

---

