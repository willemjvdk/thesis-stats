"""
Decision rule engine for mapping CSV review notes to DB decisions.
Rules are Python-based (not YAML) for type safety and testability.
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class DecisionRule:
    """A rule that maps a resolution_note to a review decision.

    Rules are checked in order; first match wins.
    The catch-all rule (r".*") should be last.
    """
    name: str
    when_note: str
    status: Optional[str]
    resolution: str
    apply_proposed_fix: bool = False


DEFAULT_RULES: list[DecisionRule] = [
    DecisionRule("autofix_ok", r"Correct autofix", "accepted", "Correct autofix."),
    DecisionRule("rerun", r"(?i)rerun", "rejected", "Catastrophic error, needs rerun."),
    DecisionRule("manual_check", r"(?i)manual check", "accepted", "Manual check OK."),
    DecisionRule("fixed_with_value", r"(?i)fix to|proposed fix", "fixed",
                 "Fixed from proposed value.", apply_proposed_fix=True),
    DecisionRule("ignore_expected", r"(?i)ignore|expected", "accepted",
                 "Expected behaviour, no action needed."),
    DecisionRule("empty", r"^$", "accepted", "Correct autofix (empty note)."),
    DecisionRule("unknown", r".*", None, ""),
]


def classify_note(
    note: str,
    rules: Optional[list[DecisionRule]] = None,
) -> Optional[tuple[str, str, bool]]:
    """Map a resolution_note to (status, resolution, apply_proposed_fix) or None to leave open.

    Rules are checked in order; first match wins.
    A None status means "leave open" (the catch-all).
    """
    rules = rules or DEFAULT_RULES
    stripped = note.strip() if note else ""
    for rule in rules:
        if re.search(rule.when_note, stripped):
            if rule.status is None:
                return None
            return (rule.status, rule.resolution, rule.apply_proposed_fix)
    return None
