Extract only the study design metadata from this CVD (cardiovascular disease) clinical trial paper.

## Output JSON format
```json
{
  "cov_nr": "XXXX",
  "n_arms": 2,
  "arm_labels": ["control", "treatment"]
}
```

## Rules
- `cov_nr`: 4 digits, zero-padded on the left (e.g., `0042`). Extract from the filename.
- `n_arms`: Count of ALL arms including control. Count each distinct group for which the paper reports **separate baseline data**. If a study has subgroups with separate data tables (e.g., "chronic HT self-monitoring" and "gestational HT self-monitoring"), count each subgroup as a separate arm.
- `arm_labels`: Brief descriptions of each arm (e.g., `"usual care"`, `"cardiac rehab"`, `"telemonitoring"`)
- Output ONLY valid JSON, no explanation, no markdown code blocks
