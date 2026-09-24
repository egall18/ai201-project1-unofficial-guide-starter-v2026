# The Unofficial Guide

Erik Gallardo-Cruz — corpus: `campus_life`

---

# Unit 1

## What This Does

This answers questions about campus life at one university, from the
`campus_life` corpus: 88 short documents in which students describe halls of
residence, dining halls, courses, and the administrative rules nobody explains
properly. It handles questions with a specific answer somewhere in those
documents — how you pay for laundry in a particular hall, how many hours a week
a particular course takes, what time the library closes during reading week —
and answers them by retrieving the relevant documents and quoting from them,
naming the file it used.

It is deliberately narrow. A question the documents don't cover gets refused
rather than guessed at, through two layers: a distance cutoff that stops
questions with nothing close in the corpus, and a grounding instruction that
catches the ones that get past it. Asked what the tuition is — which these
documents never say — it says it doesn't have enough information instead of
inventing a number.

## Chunking Strategy

**Chunk size:** 600 characters
**Overlap:** 0 characters

I measured the corpus before picking either number. `campus_life` is 88
documents of 178 to 549 characters, 2 to 5 paragraphs each, median paragraph 93
characters. Every document is one person writing about one thing: one hall, one
course, one dining hall.

**600 because the longest document is 549.** That puts the cutoff just above the
corpus with 51 characters of margin, which makes "one post, one chunk" a
decision rather than an accident. At the default of 800 the same thing happened,
but only because 800 was comfortably larger than anything here — I'd have been
taking credit for a number I never chose. Going smaller would split posts that
are already a single thought, and the median paragraph of 93 characters is far
too small to stand alone: "Best time to do laundry here is Tuesday or Wednesday
morning" is only a fact if you know which building.

**Overlap 0 because nothing gets cut.** Overlap exists so a sentence sliced down
the middle is still readable in one of the two pieces. My `split_documents`
never splits inside a paragraph, and prepends the document's title line to every
chunk, so there is no severed context to rescue. Keeping overlap would copy text
into the index twice, and near-duplicate chunks are the exact problem this
corpus already has too much of — seven laundry files that differ by one line.

**What the chunker actually does**, in `chunker.py::split_documents`:

1. Never cut inside a paragraph; pack whole paragraphs up to the budget.
2. Prepend the document's title line to every chunk, including continuations.
3. A document that fits stays whole.

Rule 2 is the one I care about. That title line is the only thing separating
`housing_aldridge_hall_laundry.txt` from six near-identical siblings, and it
appears exactly once, at the top. A chunk that loses it still retrieves for a
laundry question and still reads like a complete answer — which is worse than
not retrieving at all. It's acceptance criterion 4, enforced in the chunker
rather than hoped for.

**What changed, and what didn't.** On `campus_life` this produces 88 chunks,
each byte-identical to its source document — the same count the starter's
`fallback_split` produced. I want to be straight about that rather than dress it
up: for this corpus the new chunker's output is the old chunker's output, and
the work is in the reasoning and in the guarantees, not in a different number.

The difference shows on documents long enough to actually split. Running both
over `advice_threads`, `fallback_split` turns 23 documents into 26 chunks, and
three of those are trailing fragments that are strict suffixes of the chunk
before them — 59, 113, and 2 characters long. The 2-character one is `t.`. None
carries a title, all duplicate text already in the index, and all three exist
only because a document happened to land between `CHUNK_SIZE - CHUNK_OVERLAP`
and `CHUNK_SIZE`. My chunker gives 27 chunks with no fragments, every one
carrying its thread title and ending at a paragraph boundary.

**I changed my mind once.** My first version kept the title only on
continuation chunks, on the grounds that the first chunk already starts with it.
That's true but fragile — it makes chunk 0 a special case, and the first time a
document's opening paragraph is long enough to be split on its own, chunk 0
stops being special and silently loses the guarantee. Prepending the title
unconditionally means the rule holds for every chunk by construction, and for
documents that fit it reconstructs the original text exactly, which is how I can
claim all 88 are byte-identical.

## Sample Chunks

From `python app.py chunks -n 5`, 5 of 88.

**Chunk 1** — source: `admin_add_drop_deadline.txt#0` — produced by: `chunker.py::split_documents`

```
On the add/drop deadline

You can add a course through the end of the second week. Dropping is a longer window — through the end of week six — but a drop after week two shows as a W on your transcript. Nothing anywhere on the registrar's site says this plainly, and students find out from each other.
```

**Chunk 2** — source: `course_biol_160.txt#0` — produced by: `chunker.py::split_documents`

```
BIOL 160 Cell Biology

I lived here my sophomore year. Format is lecture three times a week with a weekly lab. Assessment: four unit tests and a cumulative final. Not curved.

Expect 9 to 11 hours a week, the heaviest first-year course by reputation.

The one piece of advice: the unit tests come fast, roughly every three weeks; falling behind once is very hard to recover from.
```

**Chunk 3** — source: `course_hist_118_workload.txt#0` — produced by: `chunker.py::split_documents`

```
Workload for HIST 118 Modern World History

People keep asking so: a lot of reading, about 120 pages a week, but no problem sets. That's real time, not optimistic time.

It's front-loaded — the first month is heavier than the rest, partly because you're learning the format.
```

**Chunk 4** — source: `dining_pellew_dining_hall_followup.txt#0` — produced by: `chunker.py::split_documents`

```
Re: Pellew Dining Hall

Adding to what people have said about Pellew Dining Hall. The wait figure of 12 to 18 minutes at peak matches what I've seen. If you're trying to eat between classes, go before 11:45 and it's a different building entirely.

Also worth saying: the furthest hall from anywhere, next to the athletics centre. Nobody tells you this at orientation.
```

**Chunk 5** — source: `housing_innisfree_hall.txt#0` — produced by: `chunker.py::split_documents`

```
Innisfree Hall — what it's actually like

Transferred in last year, so take this with a grain of salt. Built 1991, renovated 2022. Rooms are doubles arranged as pairs sharing one bathroom between two rooms.

The good: the shared-bathroom-between-two-rooms arrangement is the best compromise on campus.

The bad: no air conditioning, which matters for the first three weeks of September.

Laundry costs $1.75 wash, $1.75 dry, app-based. On noise: moderate; the building is L-shaped and the short wing is much quieter.
```

Every one of the five opens with the line that says what it's about, and every
one ends at a paragraph boundary. Checking the rule across the whole index
rather than the sample: 88 of 88 chunks contain their source document's first
line verbatim, which is acceptance criterion 4.

Chunk 5 is the one worth reading twice. Innisfree charges **$1.75 wash** — the
same as Aldridge. That collision is why my test question about Aldridge laundry
asks how you pay rather than what it costs, and it's the whole reason criterion
4 exists: strip the title line off that chunk and there is nothing left in it
that says which building it describes.

## Sample Answer

**Question:** How do you pay for laundry in Aldridge Hall?

**Answer:**

```
  (best distance 0.293, cutoff 0.75)

In Aldridge Hall, laundry is card only.

Source: housing_aldridge_hall.txt (and housing_aldridge_hall_laundry.txt)

Sources retrieved: housing_aldridge_hall.txt, housing_aldridge_hall_laundry.txt, housing_calder_annexe_laundry.txt, housing_innisfree_hall_laundry.txt, housing_old_brewhouse_laundry.txt
```

I picked this one because it's the hardest question I wrote. Look at the
retrieved sources: alongside the two Aldridge files it pulled back the laundry
documents for Calder Annexe, Innisfree Hall and Old Brewhouse — three
near-identical documents that differ from the right one by a single line. It
answered from the correct building anyway, and cited both Aldridge files rather
than a sibling.

**My relevance cutoff:** 0.75

| Question | In corpus? | Best distance |
|---|---|---|
| After what time does the salad bar at Kestrel Commons wilt? | Yes | 0.229 |
| How late in the term can I declare a course pass/fail? | Yes | 0.215 |
| How do you pay for laundry in Aldridge Hall? | Yes | 0.293 |
| How many hours a week outside class should I expect CS 210 to take? | Yes | 0.270 |
| What time does the library close during reading week? | Yes | 0.412 |
| What is the capital of Mongolia? | No | 0.825 |
| How do I change the oil in a diesel engine? | No | 0.934 |
| Who won the 1994 World Cup? | No | 0.886 |
| What is the recommended dosage of ibuprofen for a headache? | No | 0.844 |
| How do I write a for loop in Rust? | No | 0.896 |

The two groups don't overlap at all: in-corpus tops out at 0.412, out-of-corpus
bottoms out at 0.825, a gap of 0.413 with nothing in it. The midpoint is 0.618,
and the starter's default of 0.6 sits almost exactly there.

**So I nearly kept 0.6, and it would have been wrong.** The gap looks that clean
because both groups are rigged: I wrote the five in-corpus questions already
knowing the answers, and the five out-of-scope ones are about Mongolia and
diesel engines. Neither group looks like a question a real student types.

So I measured a third group — ten vaguer questions this corpus genuinely does
answer:

| Question | Best distance | Nearest document |
|---|---|---|
| laundry | 0.408 | `housing_old_brewhouse_laundry.txt` |
| is it loud at night | 0.514 | `housing_morrow_house_noise.txt` |
| can I get my money back on a textbook | 0.555 | `money_textbooks.txt` |
| what happens if I fail something | 0.613 | `admin_pass_fail_option.txt` |
| is parking a nightmare | 0.613 | `admin_parking_permits.txt` |
| how much walking is there | 0.631 | `transit_walking.txt` |
| how do I get a doctor's appointment | 0.636 | `health_center.txt` |
| do I need a coat | 0.663 | `winter_gear.txt` |
| where do people study | 0.680 | `course_econ_101.txt` |
| what's the food like | 0.706 | `dining_kestrel_commons.txt` |

Every one of those is answerable from my documents, and **a cutoff of 0.6
refuses six of them.** That's the number the curated groups hid.

0.75 sits above that 0.706 ceiling and below the 0.825 floor of the out-of-scope
group. It admits the vague-but-answerable and still refuses all five out-of-scope
questions, so criterion 3 holds.

**What 0.75 does not fix, and no number would.** I also tried eight
campus-flavoured questions the corpus can't answer:

| Question | Best distance |
|---|---|
| how much is tuition | 0.552 |
| what is the acceptance rate | 0.699 |
| when is spring break | 0.708 |
| where is the football stadium | 0.717 |
| how do I get a scholarship for graduate school | 0.726 |
| how do I join a fraternity | 0.735 |
| who is the university president | 0.742 |
| what is the mascot | 0.898 |

These land *inside* the in-corpus range — "how much is tuition" at 0.552 is
closer than seven questions my corpus genuinely answers. There is no threshold
that separates them, because distance measures whether text looks similar, not
whether it contains an answer. Lowering the cutoff to exclude them would refuse
most of the real questions in the table above.

That's what the second layer is for, and `gate.py` says so outright: the gate
catches the clear misses, the prompt catches the near ones. I checked both ends
rather than assuming:

```
$ python app.py ask "who is the university president"
  (best distance 0.742, cutoff 0.75)
I don't have enough information to answer who the university president is.

$ python app.py ask "how much is tuition"
  (best distance 0.552, cutoff 0.75)
I don't have enough information to answer this question.
```

Both passed the gate and both were refused by the model, from documents that
genuinely don't contain the answer. So 0.75 is set to do the gate's actual job —
stopping the clear misses — rather than a job it can't do.

**One prediction I got wrong.** In criterion 3 I wrote that the ibuprofen
question would be the out-of-scope one most likely to slip through, because
`health_center.txt` gives it neighbouring vocabulary. It came back at 0.844, the
second *furthest* of the five, and its nearest document was `money_textbooks.txt`
— not the health centre at all. The closest out-of-scope question was Mongolia at
0.825, matching `course_hist_118_exams.txt`, which makes sense in hindsight:
history exams, capital cities. I was reasoning about topic; the embedding was
reasoning about wording.

## How I Used AI

I built this with Claude Code (Claude Opus 5) throughout. Both moments below are
ones where what came back looked right and wasn't, and the fix came from checking
it against the corpus rather than from reading it again.

**1. The test question whose answer couldn't fail.** I asked for five test
questions with an `expects` string for each, in Milestone 2. For the laundry
question it produced the obvious thing — "What does it cost to wash a load of
laundry in Aldridge Hall?" with `expects` of `1.75` — which is a specific
question with a specific numeric answer, exactly what the milestone asks for.

Before accepting it I grepped every `expects` string against all 88 documents to
see how many could match. `1.75` matched **nine**, because Innisfree Hall charges
$1.75 to wash as well. An answer that retrieved the wrong building entirely would
have contained "1.75" and scored as correct. The question was fine; the way of
checking it was broken, and the whole point of writing `expects` before seeing
results is that it can fail.

I changed the question to "How do you pay for laundry in Aldridge Hall?" with
`expects` of `card only` — every other hall is app-based, coin-only, or
coin-or-card, so that string appears in the Aldridge files and nowhere else. The
general lesson went into my notes: an `expects` that matches many documents
measures luck, not retrieval. That collision is also why acceptance criterion 4
exists.

**2. The relevance cutoff that the evidence appeared to confirm.** In Milestone 4
I asked for the two groups of distances the milestone calls for. They came back
cleanly separated — my five questions at 0.215 to 0.412, the five out-of-scope
ones at 0.825 to 0.934 — with a midpoint of 0.618, and the reasoning was that the
starter's default of 0.6 sits in the gap and should stay. Every number in that
argument is correct.

It's still the wrong conclusion, because both groups are rigged. I wrote the
in-corpus questions already knowing the answers, so they reuse the documents'
own wording, and the out-of-scope ones are about Mongolia and diesel engines.
Nothing in either group resembles what a student actually types, so the clean gap
between them is an artifact of how I chose the questions.

So I measured a third group that the milestone doesn't ask for: ten vaguely
worded questions the corpus genuinely answers. They ran 0.408 to 0.706, which
means **a cutoff of 0.6 refuses six of them** — "what's the food like", "where do
people study", "do I need a coat". I set the cutoff to 0.75 instead. The change
wasn't catching a wrong number; it was noticing that a confident argument had
been built on a sample chosen to make it true.

<!-- ── Stretch features ─────────────────────────────────────────────────────
     Doing one? Say so here BEFORE you start. A feature this README never
     claims earns nothing.
     ───────────────────────────────────────────────────────────────────────── -->

---

# Unit 2

<!-- These sections get ADDED to what's already above. Don't delete or rewrite
     unit 1 — the point is that someone can see what you said before you knew
     how it went. -->

## Run Log — Before

`python run_eval.py --label before` — full log in
`results/run_2026-09-23_1753_before.md`. Corpus `campus_life`, top-k 5, cutoff
0.75, caching off, 15 model calls.

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET |
| 2. Every answer names a source | 5 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET |
| 3. Gate stops out-of-corpus questions | 4 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET |
| 4. Every chunk carries its title line | 88 of 88 | 88 of 88 | 88 of 88 | 88 of 88 | MET |
| 5. Answer contains the `expects` string | 4 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET |

Criteria 1, 3 and 4 are measured once rather than three times. Retrieval is
deterministic, the gate is a comparison against a fixed number, and chunking
doesn't depend on the question — three passes would produce the same three
answers, so the same figure goes in all three columns.

### Real output

**Criterion 1** — retrieval, `store.py::search`, over chunks from
`chunker.py::split_documents`. The Aldridge laundry question, the hardest one I
wrote:

```
### How do you pay for laundry in Aldridge Hall? — run 1
- Best distance: 0.2928 (passed the gate)
- Sources retrieved: housing_aldridge_hall.txt, housing_aldridge_hall_laundry.txt, housing_calder_annexe_laundry.txt, housing_innisfree_hall_laundry.txt, housing_old_brewhouse_laundry.txt
```

Three rival halls came back alongside the right one — Calder Annexe, Innisfree
and Old Brewhouse — which is the near-duplicate competition criterion 1 was
written to catch. `housing_aldridge_hall_laundry.txt` is in the set, so it
counts.

**Criterion 2** — the source line, produced by `generate.py::answer_from_chunks`
under the instruction in `generate.py::GROUNDING_INSTRUCTION`:

```
In Aldridge Hall, laundry is card only. 

Source: housing_aldridge_hall_laundry.txt (also mentioned in housing_aldridge_hall.txt)
```

All 15 answers across the three runs named a filename that exists in
`corpora/campus_life/documents/`.

**Criterion 3** — the gate, `gate.py::check` via
`run_eval.py::check_out_of_scope`:

```
| Out-of-scope question | Best distance | Gate |
|---|---|---|
| What is the capital of Mongolia? | 0.825 | refused |
| How do I change the oil in a diesel engine? | 0.934 | refused |
| Who won the 1994 World Cup? | 0.886 | refused |
| What is the recommended dosage of ibuprofen for a headache? | 0.844 | refused |
| How do I write a for loop in Rust? | 0.896 | refused |
```

Refused 5 of 5. The closest was 0.825 against a cutoff of 0.75 — a margin of
0.075, the narrowest of the five.

**Criterion 4** — chunking, `chunker.py::split_documents`, checked across the
whole index rather than the printed sample:

```
CRITERION 4 — chunks carrying their title line: 88 of 88
```

**Criterion 5** — the answer text, scored by `scorer.py::judge`:

```
### What time does the library close during reading week? — run 1
- Best distance: 0.4115 (passed the gate)

The library closes at 10pm during reading week (from study_library_hours.txt).
```

`expects` for that question is `10pm`, and the answer contains it. 15 of 15
across the three runs.

### A bug I found in my own scorer before trusting any of this

The first version of `scorer.py` read:

```python
return expects.strip().lower() in (answer or "".lower)
```

The `.lower` is inside the parentheses and never called. Two consequences: the
answer is never lower-cased, so the case-insensitive match criterion 5 specifies
wasn't happening, and an empty or `None` answer raises
`TypeError: argument of type 'builtin_function_or_method' is not iterable`
instead of scoring as a miss.

```
expects 'card only' vs answer 'CARD ONLY'  -> False   (should be True)
empty answer                               -> TypeError
```

Fixed to `(answer or "").lower()` and re-ran everything above with the corrected
scorer. The numbers didn't change — all 15 answers happened to contain their
`expects` string in matching case, so the bug could only ever have produced
false *misses*, and there were none to produce. But the run log I had before the
fix was evidence from an instrument I hadn't checked, and I'd rather report
numbers I can defend than numbers that happened to be right.

## Verdicts

Judged against the targets in `criteria.md` as written in unit 1, not against
anything I'd write now.

| # | Criterion | Verdict | How I decided |
|---|---|---|---|
| 1 | Retrieved chunk contains the answer | MET | Target 4 of 5; got 5 of 5. Deterministic, so "held on every run" and "held once" are the same claim here. Scored as: the document containing that question's `expects` string is among the five retrieved — checked by substring, not by reading the chunks and deciding. |
| 2 | Every answer names a source | MET | Target 5 of 5, the only target with no slack. All 15 answers across three runs contained a filename that exists in `corpora/campus_life/documents/`. I checked existence rather than shape, because the criterion was written to exclude a filename the model invented. |
| 3 | Gate stops out-of-corpus questions | MET | Target 4 of 5; the gate refused all five. The only judgement was fixed in advance: the five questions are the ones in `OUT_OF_SCOPE`, decided before any results, so "clearly don't cover" wasn't something I got to interpret on the day. |
| 4 | Every chunk carries its title line | MET | Target 88 of 88; got 88 of 88. Substring check of each source document's first line against its chunk, across the whole index rather than the printed sample of five. See the note below — this one passing means less than it looks. |
| 5 | Answer contains the `expects` string | MET | Target 4 of 5; got 5 of 5 on all three runs. Scored by `scorer.py::judge`, which I had to fix before I could trust it — the case-insensitive match the criterion specifies wasn't happening. Same result after the fix. |

### Nothing missed, so: were the targets set too low?

Three of the five cleared their target with room to spare, and I'd rather name
which ones were soft than present a clean sweep as if it were all earned.

**Criterion 4 was too easy, and I knew it when I wrote it.** I said so in
`criteria.md` at the time: at `CHUNK_SIZE` 600 nothing splits, so 88 of 88 is
true by construction — `split_documents` prepends the title line to every chunk,
and the only way to fail is to break the chunker itself. I wrote it as a
guardrail against a chunk-size change I then never made. It has cost me nothing
and taught me nothing, which is exactly the failure mode the brief warns about.

**Criterion 3 measures the easy half of the problem.** It passed 5 of 5, but the
five `OUT_OF_SCOPE` questions are about Mongolia, diesel engines and the 1994
World Cup — a corpus about one campus was never going to rank them close. The
questions that actually defeat the gate are the campus-flavoured ones I measured
in unit 1: "how much is tuition" at 0.552 and "who is the university president"
at 0.742 both sail past a 0.75 cutoff and are stopped by the grounding
instruction instead. Criterion 3 reads like it measures "the system refuses what
it can't answer". It measures "the system refuses questions about other
planets."

**Criteria 1 and 5 were pitched at 4 of 5 for a reason that didn't materialise.**
I expected the near-identical document families to cost me one: seven laundry
files differing by a single line, eight workload files in the same shape.
Retrieval pulled three rival halls' laundry documents alongside the right one and
still ranked Aldridge first. The prediction was wrong in the system's favour.

**The one I'd tighten, and to what.** Criterion 3, from "at least 4 of 5" to
**"at least 4 of 5, where the five questions are campus-flavoured questions the
corpus does not answer — tuition, term dates, admissions, athletics, campus
governance"**. That's the same number against a harder test, not a higher bar
against the same one, and it would fail today — not narrowly. I measured the
replacement set against the live index rather than asserting it:

```
cutoff 0.75
  0.552  PASSED gate  how much is tuition
  0.699  PASSED gate  what is the acceptance rate
  0.708  PASSED gate  when is spring break
  0.717  PASSED gate  where is the football stadium
  0.742  PASSED gate  who is the university president

gate would refuse 0 of 5 -- target is 4 of 5
```

**Zero of five.** Every one of those is a question this corpus cannot answer,
and the gate passes all five straight through to the model. Criterion 3 scored
5 of 5 against the questions I picked and would score 0 of 5 against questions a
student would actually ask — same criterion, same cutoff, same system, only a
test that isn't chosen in my favour.

I'm recording that here rather than editing `criteria.md`, because a target I
rewrite after watching it pass is worth less than one that held. The number to
carry forward is 0 of 5.

## Diagnoses

**Nothing missed.** All five criteria MET, and the Verdicts section above says
which targets were soft and which one I'd tighten. So there is no failing
criterion to trace back to a stage.

There is, however, a measured failure — the one the criteria don't catch. The
gate refuses **0 of 5** campus-flavoured questions the corpus cannot answer.
That's a real defect with a real mechanism, and diagnosing it is worth more than
writing "nothing to diagnose" under a heading.

### The miss: the gate can't tell "close" from "answerable"

**Stage: embedding.** Not retrieval, and not the gate — both of those work
exactly as written. `store.py::search` returns the nearest chunks and
`gate.py::check` compares the best distance to a number. Neither is broken. The
defect is in what the numbers they're passing around actually mean.

**The mechanism.** `all-MiniLM-L6-v2` encodes what a passage is *about*. It does
not encode whether a passage *answers a question*, and nothing downstream can
recover a distinction the vector never carried. Here is the evidence, measured
against the live index — distance, whether the corpus can actually answer it,
and how many content words the question shares with the document it matched:

```
  dist  answerable  overlap  question -> nearest document
 0.552       False        0  'how much is tuition'            -> admin_transcript_requests.txt
 0.699       False        0  'what is the acceptance rate'    -> admin_pass_fail_option.txt
 0.708       False        0  'when is spring break'           -> winter_gear.txt
 0.717       False        0  'where is the football stadium'  -> housing_fenwick_court.txt
 0.742       False        0  'who is the university president'-> admin_wifi_and_accounts.txt

 0.514        True        1  'is it loud at night'            -> housing_morrow_house_noise.txt   ['loud']
 0.631        True        1  'how much walking is there'      -> transit_walking.txt              ['walking']
 0.663        True        1  'do I need a coat'               -> winter_gear.txt                  ['coat']
 0.680        True        1  'where do people study'          -> course_econ_101.txt              ['people']
 0.706        True        0  "what's the food like"           -> dining_kestrel_commons.txt
```

Read the two blocks against each other. **Every unanswerable question shares
zero content words with the document it matched**, and four of the five still
score better than a question the corpus genuinely answers. "How much is tuition"
lands at 0.552 — closer than *four of the five answerable questions* — against
`admin_transcript_requests.txt`, a document about transcripts costing $8. There
is no shared word. What the embedding has noticed is a shape: *official
university service, has a price*. That shape is correct, and it is not an answer.

Meanwhile "what's the food like" matched `dining_kestrel_commons.txt`, which
genuinely answers it — stir-fry station, salad bar, wait times — and scored
0.706, further away than the tuition non-answer. **In this sample the distance
ordering is anti-correlated with answerability.**

### Why no cutoff can fix it

This is the part that makes it a diagnosis rather than a complaint. The mean
pairwise distance between the 88 chunks *of my own corpus* is **0.774**:

```
corpus homogeneity: mean pairwise distance between the 88 chunks = 0.774
  (min 0.114, max 1.141)
```

Every unanswerable question above lands **nearer to its best-matching document
(0.552–0.742) than two random documents of the corpus are to each other
(0.774)**. My relevance cutoff of 0.75 already sits below the corpus's own mean
internal distance.

So asking the gate to separate "answerable" from "not" is asking a single scalar
to resolve a difference finer than the corpus's own internal spread. Lower the
cutoff and the vague-but-answerable questions go first — that was already
measured in unit 1, where 0.6 refused six of ten real questions. Raise it and
everything gets through. There is no value in between, because the two
populations overlap in the only dimension the gate can see.

### The pattern

This is **one problem, not five**. All five near-misses fail identically: a
campus-vocabulary question lands close to campus-vocabulary text, and closeness
was never evidence of an answer. It is also why criterion 3 passes 5 of 5 — the
`OUT_OF_SCOPE` questions are about Mongolia and diesel engines, so they differ
from the corpus in *both* topic and register and land at 0.825–0.934, above the
corpus's own 0.774 mean. **Criterion 3 only detects failures that are further
away than my corpus is from itself.** Anything nearer than that is invisible to
it, and "anything nearer than that" is every question a student would actually
get wrong.

### What this implies for the fix

The signal the gate needs isn't in the embedding, so the fix has to add a signal
rather than re-tune an existing one — something that asks whether the retrieved
chunks contain what was asked about, not merely whether they resemble it. That's
Milestone 4.

## The Improvement

**What I changed:** hybrid search — I added a keyword signal alongside the
vector one and used it in the relevance gate. `gate.py::check` now refuses a
question when the best distance clears the cutoff **or** when no word the
question is about appears anywhere in the retrieved chunks
(`gate.py::has_lexical_support`). One extra condition, roughly twenty lines, no
change to retrieval or to the prompt.

**Why I picked it:** my diagnosis says the embedding encodes what a passage is
*about* and carries no lexical signal at all — "how much is tuition" sits 0.552
from a document about transcripts costing $8 and shares no word with it — so the
fix has to supply the signal that was missing rather than re-tune the one that
can't carry the distinction.

### What I tried first, and why it isn't what shipped

I started with BM25 proper, since `rank-bm25` ships with the starter and the
obvious reading of "hybrid search" is to fuse a BM25 score with the vector
score. I built it and measured the scores before wiring it to anything:

```
ANSWERABLE vague      bm25 3.39 - 5.37
UNANSWERABLE campus   bm25 2.14 - 6.26
```

**The ranges overlap completely.** "When is spring break" scores 6.26, higher
than every answerable question in the group, because BM25 rewards term frequency
and both "spring" and "break" occur in the corpus in unrelated senses. Weighted
keyword scoring measures how *much* vocabulary overlaps; it can't tell that the
overlap is irrelevant. A threshold on that number would have refused real
questions and let tuition through.

What does separate the groups is the weaker question: does *any* word the
question is about appear at all. That's the version in `gate.py`. I also tested
a corpus-wide variant — is the word anywhere in the 88 documents — and it's
strictly weaker, catching 3 of 5 instead of 4 of 5, because "acceptance rate"
contains "rate", which exists in the corpus but not in anything retrieved for
that question.

I tested two other ideas and rejected both on measurement:

- **Distance margin** (best vs. mean of the top 5): answerable questions range
  0.020–0.266, unanswerable 0.011–0.084. Total overlap, no signal.
- **IDF thresholding**: "break" appears in one document and "walking" appears in
  one document — identical rarity, one unanswerable and one answerable.

### Run Log — After

`python run_eval.py --label after` — `results/run_2026-09-23_1826_after.md`.

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET |
| 2. Every answer names a source | 5 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET |
| 3. Gate stops out-of-corpus questions | 4 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET |
| 4. Every chunk carries its title line | 88 of 88 | 88 of 88 | 88 of 88 | 88 of 88 | MET |
| 5. Answer contains the `expects` string | 4 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET |

**Did it help?**

Yes — but not on the table above, and that's the honest headline. **Every
criterion reads exactly the same before and after.** All five were already MET,
so on my own acceptance criteria this change is invisible. If the five criteria
were the whole story, I'd have to report that I changed the system and nothing
moved.

The change is visible on the test my criteria couldn't see — the campus-flavoured
questions the corpus can't answer:

| | Before | After |
|---|---|---|
| Gate refuses campus-flavoured unanswerable questions | **0 of 5** | **4 of 5** |
| False refusals, my 5 test questions | 0 of 5 | 0 of 5 |
| False refusals, 5 vague real-phrasing questions | 0 of 5 | 0 of 5 |
| Criterion 3's own `OUT_OF_SCOPE` five | 5 of 5 | 5 of 5 |

```
refused  best distance 0.552 is under the 0.75 cutoff, but no word from the question appears in the retrieved text  | how much is tuition
refused  best distance 0.699 ... no word from the question appears in the retrieved text  | what is the acceptance rate
PASSED   best distance 0.708 is under the 0.75 cutoff                                     | when is spring break
refused  best distance 0.717 ... no word from the question appears in the retrieved text  | where is the football stadium
refused  best distance 0.742 ... no word from the question appears in the retrieved text  | who is the university president
```

Zero to four, with no false refusals anywhere — not on the five questions I wrote
knowing the answers, and not on the five vaguely worded ones a real student would
type. That last column is the one I was most worried about: a lexical condition
is exactly the kind of change that quietly starts refusing legitimate questions,
and it didn't.

There's a second effect worth recording. Before the change, those questions
reached the model and were refused by the grounding instruction — correctly, all
eight of eight I tested. So the user-visible answer was already right; what was
wrong was that being right depended entirely on the model choosing to obey an
instruction, and cost an API call each time. `how much is tuition` now costs
**0 model calls** instead of 1:

```
$ python app.py ask "how much is tuition"
  (best distance 0.552, cutoff 0.75)
I don't have enough information about that.
0 model calls this session
```

**How I know it's the change and not luck.** Criteria 1, 3 and 4 are
deterministic, so before and after are exact comparisons rather than samples.
The only code that moved is `gate.py` plus passing `question` into
`gate.check` at four call sites; retrieval, chunking, the index and the prompt
are untouched, and the distances in both run logs are identical to three decimal
places.

**What it didn't fix.** "When is spring break" still gets through, at 0.708. Both
"spring" and "break" appear in the corpus — "break" in one document, in an
unrelated sense — so the question has lexical support that means nothing. The
check tests whether a connection exists, not whether it's meaningful, and that
was a deliberate choice: requiring more than one matching word starts refusing
real questions. One question in five is the cost of not refusing anything real.

## What's Still Broken

<!-- For each criterion still missed after your fix: what you'd do about it,
     and why you stopped where you did.

     "I ran out of time" is fine if it's true. Pretending nothing is left is
     not.

     Milestone 5. -->

## What I'd Do Differently

<!-- Knowing what you know now — which of your five criteria would you write
     differently, and why?

     Milestone 5. -->
