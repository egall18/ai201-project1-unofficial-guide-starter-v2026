"""
The scorer: does one answer count as correct?

Acceptance criterion 5 defines this and nothing else does — "the answer text
contains that question's `expects` string, substring match, case-insensitive,
and a refusal contains no `expects` string and therefore counts as a miss."
This file is that sentence in code.

Deliberately not clever. A scorer that tries to judge whether an answer is
"really" right is a second thing to debug, and when a run log disagrees with me
I want to be certain the disagreement is the system's and not the scorer's.
"""


def judge(question: str, expects: str, answer: str, results) -> bool:
    """True when the answer contains the expected string."""
    if not expects:
        return False
    return expects.strip().lower() in (answer or "").lower()
