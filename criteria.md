# Acceptance criteria — The Unofficial Guide

Five criteria that say what "working" means for this system, written in unit 1
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"Retrieval works"* is an opinion. *"For at
least 4 of my 5 test questions, the top results include a chunk containing the
answer"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter or looser one. A reason that says something about your corpus or your
pipeline earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

---

## 1. Retrieved chunks contain the answer

For at least 4 of my 5 test questions, the retrieved chunks include one that
contains the answer.

**Scored as:** the retrieved chunks include the text of the document listed as
that question's source in `questions.py`. Every document here is shorter than
`CHUNK_SIZE`, so one document is exactly one chunk and this is a yes/no per
question, with no judgement about whether a chunk "really" answers it.

**Why this target:** 4 of 5 because two of my questions sit in families of
near-identical documents — seven laundry files, eight course workload files,
each differing from its siblings by a single line — so I expect the embedding to
confuse one of them. 3 of 5 would still pass if *both* families failed, and
that's the one failure this corpus is actually built to teach me.

<!-- Scoring note, pinned before results: every document here is shorter than
     CHUNK_SIZE (longest 549), so one document = one chunk, and I score this as
     "the document holding the expects string is among the five retrieved." -->

---

## 2. Every answer names a source

Every answer the system produces names at least one source document.

**Scored as:** the answer text contains at least one filename that exists in
`corpora/campus_life/documents/`. A filename the model invented doesn't count.
Refusals aren't answers and aren't scored.

**Why this target:** All five and not four, because
`generate.py::build_prompt` already labels every chunk `[from <filename>]`
before the model sees it, so naming a source is copying rather than
remembering. The line still comes from an instruction in
`GROUNDING_INSTRUCTION` rather than from code that appends it, so a single miss
would tell me the instruction isn't reliable — which is worth knowing, and
would be invisible at a target of 4.

---

## 3. The relevance gate stops out-of-corpus questions

When I ask a question my documents clearly don't cover, the relevance gate
stops it and the system returns "I don't have enough information about that" —
in at least 4 of 5 tries.

**Scored as:** the five questions in `OUT_OF_SCOPE` in `questions.py`, each run
once through `run_eval.py`. A question passes if the gate refuses it — nothing
about "clearly don't cover" is decided at scoring time, because the five were
fixed in advance.

<!-- The five questions are the ones in `OUT_OF_SCOPE` at the bottom of
     `questions.py`, and `run_eval.py` puts them through the gate and writes
     what happened into your run log. Swap them for your own if you'd rather —
     just keep five of them, or the "4 of 5" above has nothing to be 4 of. -->

**Why this target:** Four of the five out-of-scope questions — Mongolia, diesel
engines, the 1994 World Cup, Rust — share no vocabulary at all with a corpus
about one campus, and my one measured in-corpus distance is 0.254 against a 0.6
cutoff. I left room for one miss because the ibuprofen question is the only one
my corpus has neighbouring vocabulary for (`health_center.txt`), so it's the one
I'd expect to drift close enough to slip through.

<!-- Milestone 4: replace the 0.254 data point above with both measured groups
     and say whether the gap was clean or whether ibuprofen landed in it. -->

---

## 4. Every chunk carries its source document's title line

Every chunk in the index contains the first line of the document it came from,
word for word — all 88 of 88. The 5 printed by `python app.py chunks -n 5` go in
the README as the visible evidence.

**Scored as:** for each chunk, take the first line of its source file and check
whether that string appears in the chunk text. Substring match, no judgement.

**Why this target:** 88 of 88 and not a sample, because the title line is the
only thing that distinguishes near-identical documents — seven laundry files
differ from each other in one line, and each states its hall exactly once, in
that opening line ("Laundry in Aldridge Hall"). A chunk that has lost it still
retrieves for a laundry question and still reads like a complete answer, so it's
actively harmful rather than merely weaker, and one bad chunk out of 88 is one
too many.

<!-- Earlier version of this criterion read "the specific building, course, or
     dining hall the chunk describes is named inside the chunk text". Dropped
     before any results, because it can't be scored on chunks like
     winter_gear.txt or orientation_what_matters.txt, which name no building at
     all — a stranger would have had to ask me what I meant. The title-line
     version says the same thing about self-containment and is a substring
     check. -->



---

## 5. The answer itself says the right thing

For at least 4 of my 5 test questions, the answer text contains that question's
`expects` string from `questions.py`.

**Scored as:** substring match, case-insensitive, against the answer the system
printed. A refusal contains no `expects` string and therefore counts as a miss.

**Why this target:** 4 of 5 because Q3 and Q4 each sit in a family of
near-identical documents and I'll accept the retrieval confusing one of them,
while both missing would be a systematic inability to tell near-duplicates
apart — a diagnosis I want rather than a result I'd excuse. I set it at 4 rather
than 3 because this is the criterion I'd be most disappointed to miss: it's the
only one that asks whether the thing the reader actually reads is correct.

<!-- Judgement call pinned before results: Q1's fact appears in both
     dining_kestrel_commons.txt and its _followup, both genuinely correct, so
     either source is fine — this criterion only looks at the answer text.

     This one replaced "the source it names is the right source" (4 of 5, the
     named document is the one holding the expects string, not a sibling).
     Swapped before any results, because running the set past the self-check
     showed that nothing at all checked the ANSWER: criterion 1 checks
     retrieval, 2 checks that a source is named, and a system could retrieve
     perfectly, cite correctly, and still write something wrong. This version
     also catches over-refusal, which nothing else did — if I set THRESHOLD too
     low, criterion 3 scores a perfect 5 of 5 while the system refuses
     everything, and only this criterion would notice.

     What the set no longer catches: a correct answer citing the wrong sibling
     document. Criterion 2 would pass it. That's the first thing I'd add if I
     had a sixth. -->



---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 2 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 1. Retrieved chunks contain the answer

         For at least 4 of my 5 test questions, the retrieved chunks include
         one that contains the answer.

         **Why this target:** ...

         > **Revised in unit 2:** For at least 4 of 5 questions, the top three
         > results contain the answer.
         >
         > **Why revised:** I couldn't judge "the chunks include one that
         > contains the answer" the same way twice — I scored two questions
         > differently on Monday than on Wednesday. The new version is
         > something I can actually check.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said 4 of 5 but got 2 of 5, so 2 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.

     The whole reason the originals stay visible is so someone can see what you
     said before you knew the answer.
     ───────────────────────────────────────────────────────────────────────── -->
