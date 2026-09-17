"""
Your test questions.

Milestone 2 asks you to write five questions your system should be able to
answer from your corpus, specific enough to have a right answer.

  ✗ "What are good dining halls?"          — no right answer
  ✓ "What do students say about wait times at Commons during lunch?"

Fill in `QUESTIONS` below. `expects` is a word or short phrase you'd expect a
correct answer to contain — you'll use it in unit 2 when you build a scorer,
and having written it now means you decided what "correct" meant before you saw
any results.

`OUT_OF_SCOPE` holds five questions your documents clearly don't cover. You
need these in Milestone 4 to find where your relevance cutoff belongs, and
again in unit 2, where `run_eval.py` runs them through the gate and writes what
happened into your run log — that's the evidence for criterion 3.

Swap them for your own if you like. Keep five of them either way: criterion 3
names a target of "4 of 5", and four of three is not a thing.
"""

QUESTIONS = [
    # One per document family — dining, admin, housing, courses, library — so a
    # failure points at a kind of document rather than at one unlucky file.
    # Every `expects` is a number or a date, because those are either in the
    # answer or they aren't. Nothing here can be answered by a sentence that
    # sounds right.

    # dining_kestrel_commons.txt, and again in its _followup. The only fact in
    # the corpus stated twice in two files, which makes it the one question
    # where I get to see what retrieval does with a duplicate.
    {"question": "After what time does the salad bar at Kestrel Commons wilt?",
     "expects": "1:30"},

    # admin_pass_fail_option.txt. The deadline is the whole point of the
    # document — it's late enough that you can decide after your midterm.
    {"question": "How late in the term can I declare a course pass/fail?",
     "expects": "week eight"},

    # housing_aldridge_hall_laundry.txt. Seven buildings have a laundry file
    # and they are near-identical boilerplate — only the price and payment line
    # differs — so grabbing the wrong hall gives a confident wrong answer
    # rather than an obvious miss.
    #
    # Asking the PRICE would have been the natural question, and it's the wrong
    # one: Innisfree also charges $1.75 to wash, so "1.75" can't tell a correct
    # answer from a lucky one. Payment method is unique to this hall — everyone
    # else is app-based, coin-only, or coin-or-card.
    {"question": "How do you pay for laundry in Aldridge Hall?",
     "expects": "card only"},

    # course_cs_210_workload.txt. Eight courses have a workload file in the
    # same shape, so this is the same wrong-neighbour risk as the laundry one.
    {"question": "How many hours a week outside class should I expect CS 210 to take?",
     "expects": "8 to 10"},

    # study_library_hours.txt. Reading week closes EARLIER than term, which is
    # backwards — so an answer that guesses from common sense gets it wrong.
    {"question": "What time does the library close during reading week?",
     "expects": "10pm"},
]

# Questions from a different world entirely. Your gate should refuse all five.
#
# There are five of these because criterion 3 in criteria.md names a target of
# "at least 4 of 5" — you need five things to try before you can report 4 of 5.
# `run_eval.py` runs these through retrieval and the gate on every eval and
# records what happened, so criterion 3 has evidence in the run log alongside
# the others. They cost no model calls: a refusal never reaches the model.
OUT_OF_SCOPE = [
    "What is the capital of Mongolia?",
    "How do I change the oil in a diesel engine?",
    "Who won the 1994 World Cup?",
    "What is the recommended dosage of ibuprofen for a headache?",
    "How do I write a for loop in Rust?",
]


def answered() -> list[dict]:
    """The questions you've actually filled in."""
    return [q for q in QUESTIONS if q.get("question", "").strip()]
