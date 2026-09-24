"""
The relevance gate.

This runs *before* the model does. It looks at how close the best retrieved
chunk actually is, and if nothing came back close enough it refuses the
question outright.

Why this exists as its own step, rather than just asking the model nicely to
admit when it doesn't know: if you only ask nicely, it will sometimes ignore
you and write something confident and wrong. Those answers are much harder to
catch than obvious errors. Deciding in your own code when there's nothing worth
answering from is more reliable than hoping.

You keep the polite instruction too — it's in generate.py — but as a second
layer. The gate catches the clear misses; the prompt catches the near ones.
"""

import re
from dataclasses import dataclass

import config
from store import Result

REFUSAL = "I don't have enough information about that."

# Words that carry no evidence about what a question is asking for. Everything
# here is either grammar or so common in a corpus of student advice that its
# presence tells you nothing. Kept deliberately short: the check below only
# needs ONE surviving word to match, so over-trimming this list is what would
# cause a false refusal, and the list was tested both with and without the
# borderline entries ("like", "need") to confirm neither way refuses a question
# the corpus can answer.
_STOPWORDS = frozenset(
    """
    a an and any are at be can do does expect for get go got how i if in is it
    like many much my need of on or should some that the there this to what
    when where who with you your
    """.split()
)


def _content_words(question: str) -> list[str]:
    """The words in a question that actually say what it's about."""
    words = re.findall(r"[a-z]+", question.lower())
    return [w for w in words if w not in _STOPWORDS and len(w) > 2]


def has_lexical_support(question: str, results: list[Result]) -> bool:
    """
    Does any word the question is *about* actually appear in what came back?

    The second signal, and the reason this file changed in unit 2. Distance
    says the retrieved text resembles the question. It cannot say the text
    contains what was asked for — "how much is tuition" sits 0.552 from a
    document about transcripts costing $8, sharing no word with it.

    One matching word is enough. The check is looking for the absence of any
    lexical connection at all, which is a much weaker claim than relevance and
    a much safer one: requiring more than one word starts refusing real
    questions, and this is only ever meant to catch the questions the corpus
    has no vocabulary for.
    """
    words = _content_words(question)
    if not words:
        return True  # nothing to check against; don't refuse on no evidence
    haystack = " ".join(r.text.lower() for r in results)
    return any(word in haystack for word in words)


@dataclass
class GateDecision:
    passed: bool
    best_distance: float
    threshold: float
    lexical_support: bool = True

    @property
    def explanation(self) -> str:
        if self.passed:
            return (
                f"best distance {self.best_distance:.3f} "
                f"is under the {self.threshold} cutoff"
            )
        if not self.lexical_support:
            return (
                f"best distance {self.best_distance:.3f} is under the "
                f"{self.threshold} cutoff, but no word from the question "
                f"appears in the retrieved text — refusing"
            )
        return (
            f"best distance {self.best_distance:.3f} "
            f"is over the {self.threshold} cutoff — refusing"
        )


def check(
    results: list[Result],
    threshold: float | None = None,
    question: str | None = None,
) -> GateDecision:
    """
    Decide whether the retrieved chunks are close enough to answer from.

    Remember: LOWER distance is better. A question passes when its best chunk
    is *under* the threshold AND at least one word it's about appears in the
    retrieved text.

    `question` is optional so that anything calling this the old way still
    works — without it the lexical check is skipped and the decision is the
    distance alone, which is what this did before unit 2.
    """
    threshold = config.THRESHOLD if threshold is None else threshold

    if not results:
        return GateDecision(passed=False, best_distance=1.0, threshold=threshold)

    best = min(r.distance for r in results)
    lexical = True if question is None else has_lexical_support(question, results)

    return GateDecision(
        passed=best < threshold and lexical,
        best_distance=best,
        threshold=threshold,
        lexical_support=lexical,
    )
