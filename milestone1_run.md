# Working log

Raw terminal output as I work through the milestones, pasted as text. Newest
entry at the bottom. Each one records the command, the output exactly as it came
back, and anything that had to change to get there.

This is my own notes file, not the submission — the submission is `README.md`,
and this is where I keep the material I'll paste into it.

## Numbers to keep

| What | Value | Where it came from |
|---|---|---|
| `advice_threads` chunk count | **26** | `app.py --corpus advice_threads chunks -n 1`, at CHUNK_SIZE 800 / OVERLAP 120 |
| Corpus I picked | **campus_life** | 88 documents; committed at Milestone 2 |

---

# Milestone 1

---

## Run 1 — 2026-09-16 18:32

Corpus: `campus_life` (the default in `config.py`)
Python 3.13.13, inside `.venv`

### `python app.py index`

```
Corpus: campus_life
  loaded   88 documents, 27,908 characters, ~317 characters per document
  chunked  88 chunks, 317 characters on average (shortest 178, longest 549), produced by chunker.py::fallback_split
  embedding 88 chunks (first run downloads the model)...
  stored   88 chunks in 4.5s

Ready. Try: python app.py ask "your question here"
```

Exit code 0. 88 documents in, 88 chunks out — one chunk per document, because
every file in this corpus is shorter than the 800-character `CHUNK_SIZE`, so
`chunker.py::fallback_split` never had a reason to split one.

### `python app.py ask "is the housing lottery random?"`

```
  (best distance 0.254, cutoff 0.6)

The housing lottery is not entirely random in the way most people assume. While rising sophomores get a number drawn at random, juniors and seniors are ordered by accumulated credit hours first, with random tie-breaks used only for ties.

Source: admin_housing_lottery.txt

Sources retrieved: admin_housing_lottery.txt, admin_parking_permits.txt, advising_registration.txt, housing_morrow_house.txt, housing_tamsin_court.txt

0 model calls this session, 1 served from cache
```

Exit code 0. Best distance 0.254 against a cutoff of 0.6, so the gate let it
through with room to spare — this question is squarely inside the corpus.

`0 model calls ... 1 served from cache` means the answer came from the response
cache rather than a fresh API call; the same question had been asked a few
minutes earlier. That is the starter saving quota while building, not a failure.
`AI201_CACHE=0` forces a real call, and evaluation runs turn the cache off on
their own.

### What had to be fixed first

Both commands failed before this run. `index` stopped right after the `chunked`
line, and `ask` then reported:

```
TypeError: Number of requested results 0, cannot be negative, or zero. in query.
```

That error is misleading — it means the collection was empty, not that a setting
was zero. The real failure was upstream, in embedding:

```
[E:onnxruntime:, sequential_executor.cc:572 ExecuteKernel] Non-zero status code returned while running CoreMLExecutionProvider ... Status Message: Error executing model: Unable to compute the prediction using a neural network model.
```

Chroma passes ONNX Runtime every execution provider the machine reports, and
`CoreMLExecutionProvider` sorts first on a Mac. CoreML fails on this machine
once it gets a real batch, so indexing died and stored nothing. `python test.py`
missed it because that check embeds a single short string, which CoreML
survives; 88 chunks it does not.

Fix — one line in `store.py::_OnnxEmbedder.__init__`:

```python
self._ef = ONNXMiniLM_L6_V2(preferred_providers=["CPUExecutionProvider"])
```

Same model, same 384 dimensions, same cosine distances, so `THRESHOLD` is
unaffected and the Milestone 4 measurements still mean what they should.

---

## Run 2 — 2026-09-16, `advice_threads` chunk count

Asked for during the session: run this against `advice_threads` regardless of
which corpus I picked, and keep the number reported before "chunks total."

### `python app.py --corpus advice_threads chunks -n 1`

```
26 chunks total. Showing 1, spread across the corpus.

Paste these into your README under Sample Chunks. The rubric asks
for the source file and the function that produced them — both are
printed for you below.

======================================================================
Chunk 1  |  source: thread_bike_commute.txt#0  |  produced by: chunker.py::fallback_split
======================================================================
THREAD: Is a bike worth it for a 20 minute walk commute?

--- reply 1 (14 votes) ---
Yeah. Cuts an 18 minute walk to about 6. The thing nobody mentions is storage — covered bike parking exists at three buildings and is full by 9am at all three.

--- reply 2 (9 votes) ---
Counterpoint, I sold mine. Between November and March the paths are either icy or salted and salt destroys a drivetrain in one season.

--- reply 3 (22 votes) ---
Both true. I keep a cheap bike for September to November and walk the rest of the year. Total cost was about $120 for the bike and I don't care what happens to it.

--- reply 4 (5 votes) ---
If you do get one, the campus does free registration and it's the only reason I got mine back after it was taken.

For each one, ask: could someone answer a question using only this,
without reading what came before or after?
```

**The number: 26.** Needed for the activity at the end of the session.

Exit code 0. The count belongs to `advice_threads` at the current `CHUNK_SIZE`
of 800 and `CHUNK_OVERLAP` of 120 — change those in Milestone 3 and it moves.

Worth keeping for Milestone 3: the chunk it printed is a whole thread, question
plus four replies, held together in one chunk. The replies disagree with each
other, and reply 3 only makes sense as a response to 1 and 2. Split that thread
down the middle and each half reads like settled advice when the document as a
whole is an argument. `campus_life` had no structure like that — every file
there was a short standalone blurb, one chunk each.

---

# Milestone 2 — test questions

Five questions written into `questions.py`, one per document family — dining,
admin, housing, courses, library — so that a failure points at a *kind* of
document rather than at one unlucky file.

Two rules I held myself to:

1. **Every `expects` is a number or a fixed phrase.** Either it's in the answer
   or it isn't. Nothing here can be satisfied by a sentence that merely sounds
   right, which is the whole point of writing these before seeing results.
2. **Written blind.** I have not run any of the five. The milestone says to
   decide what "correct" means before results exist, so tuning a question after
   watching it fail would defeat the exercise. First run is Milestone 4.

| # | Question | `expects` | Source document |
|---|---|---|---|
| 1 | After what time does the salad bar at Kestrel Commons wilt? | `1:30` | `dining_kestrel_commons.txt` (+ followup) |
| 2 | How late in the term can I declare a course pass/fail? | `week eight` | `admin_pass_fail_option.txt` |
| 3 | How do you pay for laundry in Aldridge Hall? | `card only` | `housing_aldridge_hall_laundry.txt` |
| 4 | How many hours a week outside class should I expect CS 210 to take? | `8 to 10` | `course_cs_210_workload.txt` |
| 5 | What time does the library close during reading week? | `10pm` | `study_library_hours.txt` |

## Why these five

**Q1 — the duplicate.** The wilting salad bar is the only fact in the corpus
stated twice, in `dining_kestrel_commons.txt` and again in its `_followup`.
Every other question has one home. This is the one place I get to watch what
retrieval does when two chunks are both right.

**Q2 — the buried fact.** The pass/fail deadline is late enough to decide after
your midterm, which is exactly the kind of thing the document says nobody
mentions. If the system is useful for anything, it's for this.

**Q3 — the near-identical neighbours.** Seven halls have a laundry file and
they're the same boilerplate apart from one line. Retrieving the wrong hall
doesn't produce an obvious miss, it produces a confident wrong answer, which is
the failure mode worth catching early.

**Q4 — the same trap, different family.** Eight courses have a workload file in
the same shape. If Q3 and Q4 both fail, that's one problem — near-duplicate
documents — not two.

**Q5 — the counterintuitive one.** The library closes *earlier* during reading
week than during term. An answer built on common sense rather than on the
document gets this backwards, so it catches a model that's guessing.

## One question I had to rewrite

Q3 started as "What does it cost to wash a load of laundry in Aldridge Hall?"
with `expects` of `1.75`. That's the natural question and it's the wrong one:
Innisfree Hall also charges $1.75 to wash, so `1.75` can't distinguish a correct
answer from one that retrieved the wrong building and got lucky. Checking the
string against the corpus turned up **nine** files containing `1.75`.

Payment method is unique to Aldridge — everyone else is app-based, coin-only, or
coin-or-card — so `card only` appears in the Aldridge files and nowhere else.
Same question, same document, an `expects` that can actually fail.

Worth remembering for unit 2: an `expects` that matches many documents doesn't
measure retrieval, it measures luck.

## Uniqueness check

How many of the 88 documents contain each `expects` string:

```
1. expects '1:30'       -> 2 docs: dining_kestrel_commons.txt, dining_kestrel_commons_followup.txt
2. expects 'week eight' -> 3 docs: admin_pass_fail_option.txt, course_cs_340.txt, course_cs_340_exams.txt
3. expects 'card only'  -> 2 docs: housing_aldridge_hall.txt, housing_aldridge_hall_laundry.txt
4. expects '8 to 10'    -> 2 docs: course_cs_210.txt, course_cs_210_workload.txt
5. expects '10pm'       -> 1 doc:  study_library_hours.txt
```

Q1, Q3 and Q4 match their source document plus one sibling on the same subject,
which is fine — both are right.

Q2 is the loose one. `week eight` also shows up in two CS 340 files, but about
starting a term project, not pass/fail. A pass/fail question has no good reason
to retrieve CS 340, so I'm leaving it. Flagging it here so that if Q2 ever
passes with a strange source line, I know where to look first.

## Known risk

If the model writes "week 8" instead of "week eight", Q2 scores as a miss even
though the answer is right. The document spells it out in words and answers tend
to echo the source, so I'm accepting that. If it bites in unit 2, it's a scorer
problem, not a retrieval problem — and telling those apart is the diagnosis
skill the next unit is asking for.

## Out of scope

Kept the five defaults. They're from a different world entirely — Mongolia,
diesel engines, the 1994 World Cup, ibuprofen dosage, Rust for loops — with no
campus vocabulary for retrieval to latch onto, which is what Milestone 4 needs
to find where the cutoff belongs.

---

# Milestone 2 — acceptance criteria

Criteria 1–3 came with the starter; I wrote the **why** for each. Criteria 4 and
5 are mine. All five are in `criteria.md`.

| # | Criterion | Target |
|---|---|---|
| 1 | Retrieved chunks contain the answer | 4 of 5 questions |
| 2 | Every answer names a source | 5 of 5 answers |
| 3 | Gate stops out-of-corpus questions | 4 of 5 refused |
| 4 | Every chunk says what it is about | 5 of 5 sampled chunks |
| 5 | The source it names is the right source | 4 of 5 questions |

## Criterion 4 — the one about chunks

**Every chunk names the building, course, or dining hall it describes, inside
its own text.** 5 of 5 sampled by `app.py chunks -n 5`.

The reasoning matters more than the criterion. `campus_life` is families of
near-identical documents — seven laundry files, seven noise files, eight course
workload files — and inside a family the text is the same boilerplate apart from
one line. The only thing distinguishing them is the subject name, and it appears
exactly once, in the first line: "Laundry in Aldridge Hall".

Today that line survives by accident. Longest document is 549 characters against
a `CHUNK_SIZE` of 800, so nothing ever splits and every chunk keeps its opening
line for free. **This criterion passes trivially right now** — which is exactly
why it belongs on the list before Milestone 3, not after. Short documents invite
a smaller chunk size, and the first time a document splits, its tail is orphaned:
"Best time to do laundry here is Tuesday or Wednesday morning," with no hall
named and six other chunks saying the identical thing.

5 of 5 rather than 4 of 5 because a chunk that can't name its subject isn't
weaker, it's harmful. It still retrieves for a laundry question and still reads
like an answer.

## Criterion 5 — my choice

**The source named in the answer is the document that actually contains the
answer**, not a sibling on the same subject. 4 of 5.

Criterion 2 only asks that *a* source gets named. "Laundry is $1.75, card only —
Source: housing_innisfree_hall.txt" satisfies criterion 2 completely and is
wrong. This is the one that catches it.

I picked it because I already walked into this exact trap an hour ago. My first
Q3 asked the cost of laundry in Aldridge with an `expects` of `1.75`, and
Innisfree charges $1.75 too — an answer citing the wrong building would have
scored correct. If a question I wrote myself can be fooled that easily, so can
the system. A guide that cites confidently and wrongly is worse than one that
refuses: you can check a refusal, but a wrong citation looks exactly like a
right one.

Recorded in advance so I'm not deciding it once results exist: Q1's fact lives
in both `dining_kestrel_commons.txt` and its `_followup`, both genuinely
correct, so either counts as right.

## Self-check

The course's checklist page needs a login I don't have, so I ran all five
against the standard stated at the top of `criteria.md`: does it name a number
or something plainly observable, does the **why** say something about *this*
corpus or pipeline, could I miss it, and could I score it the same way twice?

| # | Number or observable? | Why is corpus-specific? | Can I miss it? | Scores the same twice? |
|---|---|---|---|---|
| 1 | 4 of 5 | 88 docs, all under `CHUNK_SIZE`; two near-duplicate families | Yes | Yes — see note |
| 2 | 5 of 5 | Source line is a model instruction, not code | Yes | Yes |
| 3 | 4 of 5 | Ibuprofen vs. `health_center.txt` vocabulary | Yes | Yes — deterministic |
| 4 | 5 of 5 | Subject name appears once, in line one | **Not yet** | Yes |
| 5 | 4 of 5 | The `1.75` collision I hit in Q3 | Yes | Yes |

Two honest flags:

**Criterion 4 cannot currently be missed.** Nothing splits at `CHUNK_SIZE` 800,
so it's true by default. It goes live the moment I change chunking in Milestone
3, which is the point of it — but if I finish the project without ever lowering
the chunk size, this criterion will have cost me nothing and taught me nothing,
and I should say so rather than claim a pass.

**Criteria 1 and 5 are not independent.** If retrieval never surfaces the right
document, criterion 1 fails and criterion 5 fails with it, because there was no
correct source available to cite. They only come apart when retrieval succeeds
and attribution still goes wrong — which is the case I actually want to see.
Worth remembering in unit 2: if both miss together, that's *one* diagnosis at
the retrieval stage, not two.

**Criterion 1's wording** — "the retrieved chunks include one that contains the
answer" — is the vague kind the starter warns about in its unit-2 revision
example. Pinning it down now, before results: every document is exactly one
chunk, so I score it as *the document holding the `expects` string is among the
five retrieved*. Binary, and the same on Monday as on Wednesday.

---

# Milestone 2 — criteria self-check

Ran all five past the self-check. Two failed and were rewritten **before any
results existed**, which is the only time a rewrite is free.

## Per-criterion, six questions each

| # | Names a number? | Stranger could check? | Same score twice? | One thing? | Why that number? | About the system? |
|---|---|---|---|---|---|---|
| 1 | 4 of 5 ✓ | **was no** → fixed | **was no** → fixed | ✓ | ✓ | ✓ |
| 2 | 5 of 5 ✓ | was loose → fixed | ✓ | ✓ | ✓ | ✓ |
| 3 | 4 of 5 ✓ | was loose → fixed | ✓ | ✓ | ✓ | ✓ |
| 4 | 88 of 88 ✓ | **was no** → rewritten | **was no** → rewritten | ✓ | ✓ | ✓ |
| 5 | 4 of 5 ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

### What each failure was

**Criterion 1 — "the retrieved chunks include one that contains the answer."**
*Contains the answer* is exactly the kind of judgement word the self-check warns
about. On a good day I'd count a chunk that mentions the right hall; on a bad one
I'd want the number too. Added a **Scored as** line: the retrieved chunks include
the document listed as that question's source in `questions.py`. One document is
one chunk here, so it's yes/no per question.

**Criteria 2 and 3** — both checkable, but only if you already knew that "names a
source" means a filename that really exists in the corpus, and that the
out-of-corpus questions are the five fixed in `OUT_OF_SCOPE` rather than whatever
a tester dreams up on the day. Both now say so in a **Scored as** line. Criterion
2's version also rules out a filename the model invented, which the original
sentence would have accepted.

**Criterion 4 — rewritten completely.** It read "the specific building, course, or
dining hall the chunk describes is named inside the chunk text." I checked it
against the corpus and it is unscorable on `winter_gear.txt`
("What winter is actually like here") and `orientation_what_matters.txt` — those
documents name no building at all, so a stranger drawing one of them in a
5-chunk sample would have to come and ask me what I meant. That's a no on two of
the six questions.

Now: **every chunk contains the first line of its source document, word for
word — 88 of 88.** Same idea about self-containment, but it's a substring check
with nothing left to interpret, and it applies to all 88 documents rather than
to the subset that happens to be about a building. Dry run against the current
index: 88 of 88 pass, as expected, since nothing splits at `CHUNK_SIZE` 800.

## The set as a whole

**Do the five cover different parts?** Yes, after the change: chunking (4),
retrieval (1), the gate (3), and generation from two angles — that a source is
named (2) and that the answer is right (5). Loading and embedding aren't directly
covered; embedding shows up through criterion 1, since bad vectors mean bad
retrieval.

**Is one about what happens when things go wrong?** Criterion 3 — five questions
the corpus can't answer, and the gate has to stop at least four.

**One I'd be genuinely disappointed to miss?** Criterion 5. It's the only one
that asks whether the sentence a reader actually reads is correct.

**Would I be comfortable with a stranger testing against these?** This is the
question that changed the set, and the honest answer was no. Two gaps:

1. **Nothing checked the answer.** Criterion 1 checked retrieval, criterion 2
   checked that a source was named, and the old criterion 5 checked *which*
   source. A system could retrieve the right document, cite it correctly, and
   still write a wrong sentence — and all five would have passed.
2. **Nothing caught over-refusal.** If I set `THRESHOLD` too low in Milestone 4,
   the gate refuses everything. Criterion 3 then scores a *perfect* 5 of 5 while
   the system is useless. A stranger would find that in a minute.

So criterion 5 changed from *the source it names is the right source* to **the
answer text contains that question's `expects` string**. One substring check
closes both gaps: a refusal contains no `expects` string, so over-refusal now
costs me criterion 5 exactly when it's flattering criterion 3.

## What the set still doesn't catch

A **correct answer citing the wrong sibling document** — the right price with the
wrong hall name under it. Criterion 2 accepts it because a real filename is
present, and criterion 5 accepts it because the answer text is right. That was
the old criterion 5, and I traded it away knowingly: an unchecked answer is a
worse hole than an unchecked citation, and I only had five slots. It's the first
thing I'd add if I had a sixth, and it's written down in `criteria.md` so it
doesn't look like something I failed to notice.

Also uncovered: speed, and whether the loading stage drops or mangles a document.

---

# Milestone 3 — swapping in my own chunker

## What I measured first

```
campus_life:    88 docs | 178-549 chars (median 305) | 2-5 paragraphs | median paragraph 93 chars | 0 docs over 800
advice_threads: 23 docs | 317-793 chars (median 531) | 3-6 paragraphs | median paragraph 136 chars | 0 docs over 800
```

Every document is one person writing about one thing, and the median paragraph
is 93 characters — far too small to stand alone. "Best time to do laundry here
is Tuesday or Wednesday morning" is a fact only if you know the building.

## The defect I found in the starter chunker

This came out of the `advice_threads` number from the session activity: 23
documents, 26 chunks. The longest document is 793 characters and `CHUNK_SIZE` is
800, so nothing should have split. Three did:

```
thread_bike_commute.txt#1       59 chars   strict suffix of the doc: True   carries title: False
thread_first_year_regret.txt#1  113 chars  strict suffix of the doc: True   carries title: False
thread_meal_plan_tier.txt#1       2 chars  strict suffix of the doc: True   carries title: False
```

The two-character one is `t.`.

`fallback_split` advances by `chunk_size - overlap` = 680 and keeps looping
while `start < len(text)`. Any document between 680 and 800 characters therefore
gets a second chunk that is nothing but the tail of the first — already indexed,
no title, pure duplication. `campus_life` never triggers it because the longest
document is 549, but it's a real defect and it's why the count was 26 and not 23.

## The chunker I wrote

`chunker.py::split_documents`, three rules:

1. **Never cut inside a paragraph.** Pack whole paragraphs to the budget; split
   an oversized paragraph on sentence boundaries, never mid-sentence.
2. **Prepend the document's title line to every chunk**, continuations included.
3. **A document that fits stays whole.**

Rule 2 is acceptance criterion 4, enforced in the chunker rather than hoped for.

Numbers, with reasons, in `config.py`:

| Setting | Was | Now | Why |
|---|---|---|---|
| `CHUNK_SIZE` | 800 | 600 | Longest document is 549; 51 chars of margin makes "one post, one chunk" a decision instead of an accident of the default |
| `CHUNK_OVERLAP` | 120 | 0 | Nothing gets cut, so there's no severed sentence to rescue; overlap would only duplicate text into an index that already has seven near-identical laundry files |

## Results

| Corpus | `fallback_split` (800/120) | `split_documents` (600/0) | Title line present |
|---|---|---|---|
| campus_life | 88 chunks | 88 chunks, all byte-identical to their source document | 88 of 88 |
| advice_threads | 26 chunks, 3 junk fragments | 27 chunks, 0 fragments | 27 of 27 |

Being straight about it: **on campus_life my chunker's output is identical to
the starter's.** Same 88 chunks, same text. The work is in the reasoning and the
guarantees, not in a different number, and claiming otherwise would be dressing
it up.

The difference is visible where documents actually split. Same document, the two
chunkers' continuation chunk:

```
fallback_split      -> "nd it's the only reason I got mine back after it was taken."
split_documents     -> "THREAD: Is a bike worth it for a 20 minute walk commute?

                        --- reply 4 (5 votes) ---
                        If you do get one, the campus does free registration and
                        it's the only reason I got mine back after it was taken."
```

## I changed my mind once

First version prepended the title only to continuation chunks, since chunk 0
already starts with it. True, but it makes chunk 0 a special case, and the first
time an opening paragraph is long enough to split on its own, chunk 0 stops
being special and quietly loses the guarantee. Prepending unconditionally makes
the rule hold by construction — and for documents that fit it reconstructs the
original text exactly, which is what lets me claim all 88 are byte-identical.

## Discipline note

Sanity-checked the pipeline with "is the housing lottery random?" — not one of
my five test questions. Best distance 0.254, same as before re-chunking, which
is expected since campus_life chunk text didn't change. **None of my five test
questions have been run yet.** First time they run is Milestone 4.

---

# Milestone 4 — tuning retrieval and setting the cutoff

## The two groups the milestone asks for

```
IN CORPUS (my 5 test questions)          OUT OF SCOPE (the 5 in questions.py)
  0.229  salad bar / Kestrel               0.825  capital of Mongolia
  0.215  pass/fail deadline                0.934  diesel oil change
  0.293  Aldridge laundry payment          0.886  1994 World Cup
  0.270  CS 210 workload                   0.844  ibuprofen dosage
  0.412  library, reading week             0.896  for loop in Rust

worst in-corpus 0.412   best out-of-scope 0.825   gap 0.413   midpoint 0.618
```

No overlap, and the starter's default of 0.6 sits almost exactly in the middle.
I nearly stopped there.

## Why 0.6 was the wrong answer anyway

That gap is clean because **both groups are rigged**. I wrote the five in-corpus
questions already knowing the answers, so they use the documents' own wording.
The five out-of-scope ones are about Mongolia and diesel engines. Neither group
resembles what a student actually types.

So I measured a third group — ten vaguer questions the corpus genuinely answers:

```
0.408 laundry                         0.631 how much walking is there
0.514 is it loud at night             0.636 how do I get a doctor's appointment
0.555 money back on a textbook        0.663 do I need a coat
0.613 what happens if I fail something 0.680 where do people study
0.613 is parking a nightmare          0.706 what's the food like
```

**A cutoff of 0.6 refuses six of those.** Every one is answerable from my
documents. That is the number the curated groups hid, and it's the whole reason
this milestone is worth doing properly rather than accepting a default that
looks validated.

## The cutoff: 0.75

Above the vague-but-answerable ceiling of 0.706, below the out-of-scope floor of
0.825. Verified after setting it:

```
Criterion 3 (gate refuses out-of-corpus): 5 of 5   target 4 of 5
In-corpus questions reaching the model:   5 of 5
```

## What no threshold can fix

Eight campus-flavoured questions the corpus can't answer:

```
0.552 how much is tuition              0.726 scholarship for graduate school
0.699 what is the acceptance rate      0.735 how do I join a fraternity
0.708 when is spring break             0.742 who is the university president
0.717 where is the football stadium    0.898 what is the mascot
```

These sit *inside* the in-corpus range. "How much is tuition" at 0.552 is closer
than seven questions my corpus does answer. No threshold separates them, because
distance measures whether text looks similar, not whether it contains an answer.
Dropping the cutoff far enough to exclude them would refuse most of the real
questions above.

`gate.py` already says this is expected — the gate catches clear misses, the
prompt catches near ones — so I tested both ends instead of trusting it:

```
$ python app.py ask "who is the university president"
  (best distance 0.742, cutoff 0.75)     -> I don't have enough information...

$ python app.py ask "how much is tuition"
  (best distance 0.552, cutoff 0.75)     -> I don't have enough information...
```

Both passed the gate; the model refused both. The two-layer design holds, and
0.75 is set to do the gate's actual job rather than one it can't do.

## A prediction I got wrong

Criterion 3's reasoning said the **ibuprofen** question was the out-of-scope one
most likely to slip through, because `health_center.txt` gives it neighbouring
vocabulary. It came back at 0.844 — the second *furthest* of the five — and its
nearest document was `money_textbooks.txt`, not the health centre.

The closest out-of-scope question was **Mongolia** at 0.825, nearest document
`course_hist_118_exams.txt`. History exams, capital cities. I was reasoning
about topic; the embedding was reasoning about wording. Worth remembering before
I write another confident prediction about distances.

## Sample answer (README)

Used test question 3, the hardest one I wrote:

```
$ python app.py ask "How do you pay for laundry in Aldridge Hall?"
  (best distance 0.293, cutoff 0.75)

In Aldridge Hall, laundry is card only.

Source: housing_aldridge_hall.txt (and housing_aldridge_hall_laundry.txt)

Sources retrieved: housing_aldridge_hall.txt, housing_aldridge_hall_laundry.txt,
housing_calder_annexe_laundry.txt, housing_innisfree_hall_laundry.txt,
housing_old_brewhouse_laundry.txt
```

It pulled back three *other* halls' laundry documents alongside the right one —
the near-duplicate competition criterion 1 predicted is real — and answered from
the correct building anyway, citing both Aldridge files rather than a sibling.

---

# Unit 2, Milestone 1 — run log (before)

## A bug in the scorer, found before trusting the run

`scorer.py` as first written:

```python
return expects.strip().lower() in (answer or "".lower)
```

The `.lower` sits inside the parentheses and is never called.

```
expects 'card only' vs answer 'CARD ONLY'  -> False      (should be True)
empty answer                               -> TypeError
None answer                                -> TypeError
```

So the case-insensitive match criterion 5 specifies wasn't happening, and a
failed generation would crash the eval instead of scoring a miss. Fixed to
`(answer or "").lower()`, then re-ran the whole eval.

**The numbers didn't change.** All 15 answers contained their `expects` string
in matching case, so the bug could only ever have produced false misses and
there were none. The point isn't that it changed the result — it's that the
earlier run log was evidence from an instrument I hadn't checked.

## Results — everything MET

| Criterion | Target | Result | Verdict |
|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 | 5 of 5 | MET |
| 2. Every answer names a source | 5 of 5 | 5 of 5, all three runs | MET |
| 3. Gate stops out-of-corpus questions | 4 of 5 | 5 of 5 | MET |
| 4. Every chunk carries its title line | 88 of 88 | 88 of 88 | MET |
| 5. Answer contains the `expects` string | 4 of 5 | 5 of 5, all three runs | MET |

15 model calls, 9,478 tokens. Log: `results/run_2026-09-23_1753_before.md`.

## The thing to deal with in Milestone 2

**Nothing missed. Every criterion cleared its target, and three cleared it with
room to spare.** The README is direct about what that means: missing a target
costs nothing, setting one so easy you can't miss it does.

Honest read on which targets were soft:

- **Criterion 4 is the softest, and I knew it when I wrote it.** 88 of 88 is
  true by construction — `split_documents` prepends the title line to every
  chunk, so the only way to fail is to break the chunker. I wrote it as a
  guardrail for a chunk-size change I then never made. It has taught me nothing.
- **Criterion 3 passed 5 of 5, but the margin is thin where it counts.** The
  closest out-of-scope question sits at 0.825 against a 0.75 cutoff — 0.075 of
  room. And the near-miss probes from Milestone 4 (tuition at 0.552, university
  president at 0.742) are refused by the *prompt*, not the gate, so criterion 3
  isn't measuring what I'd want a stranger to think it measures.
- **Criteria 1 and 5 at 4 of 5 were set expecting the near-duplicate families to
  cost me one.** They didn't. The retrieval pulled three rival halls' laundry
  files and still ranked Aldridge first.

Milestone 2 decides what to do about that. The options, as I see them:

1. Report MET honestly, say the targets were soft, name which one I'd tighten
   and to what. The README explicitly allows this and asks for exactly that
   sentence.
2. Tighten a target now and re-run — but a target rewritten after seeing results
   is worth less than one that held, and lowering-after-missing is explicitly
   penalised. Raising-after-passing is the mirror image and I'd want to be
   careful about it.
3. Harden the *test* rather than the target: the near-miss questions are the
   real gap, and criterion 3's `OUT_OF_SCOPE` list is five questions from
   another planet. Swapping those for campus-flavoured ones the corpus can't
   answer would make criterion 3 measure the thing that actually fails.

---

# Unit 2, Milestone 2 — verdicts

All five MET, judged against the unit-1 targets as written:

| # | Criterion | Target | Result | Verdict |
|---|---|---|---|---|
| 1 | Retrieved chunk contains the answer | 4 of 5 | 5 of 5 | MET |
| 2 | Every answer names a source | 5 of 5 | 5 of 5 ×3 | MET |
| 3 | Gate stops out-of-corpus questions | 4 of 5 | 5 of 5 | MET |
| 4 | Every chunk carries its title line | 88 of 88 | 88 of 88 | MET |
| 5 | Answer contains the `expects` string | 4 of 5 | 5 of 5 ×3 | MET |

## Which targets were soft

**Criterion 4** — softest, and flagged as such in `criteria.md` when written. At
CHUNK_SIZE 600 nothing splits, so 88 of 88 is true by construction. Guardrail
for a chunk-size change I never made. Cost nothing, taught nothing.

**Criterion 3** — measures the easy half. Passed 5 of 5 against Mongolia and
diesel engines.

**Criteria 1 and 5** — pitched at 4 of 5 expecting the near-duplicate families
to cost one. They didn't; retrieval pulled three rival halls and still ranked
Aldridge first. Prediction wrong in the system's favour.

## The number worth carrying forward

I claimed in a first draft that a harder criterion-3 test would fail "four of
five". Measured it instead of asserting it:

```
cutoff 0.75
  0.552  PASSED gate  how much is tuition
  0.699  PASSED gate  what is the acceptance rate
  0.708  PASSED gate  when is spring break
  0.717  PASSED gate  where is the football stadium
  0.742  PASSED gate  who is the university president

gate refuses 0 of 5
```

**Zero.** Not four. The gate passes every campus-flavoured unanswerable question
straight to the model. Criterion 3 scores 5 of 5 on the questions I picked and
0 of 5 on questions a student would actually ask.

That's the honest state of the system going into Milestone 3, and it's a
sharper finding than any of the five verdicts.

The tightening I'd make, recorded but NOT applied to criteria.md: criterion 3
keeps "at least 4 of 5" but the five questions become campus-flavoured ones the
corpus can't answer. Same number, harder test. Rewriting a target after watching
it pass is worth less than one that held.

---

# Unit 2, Milestone 3 — diagnosis

No criterion missed, so the Diagnoses section diagnoses the failure the criteria
don't catch: the gate refuses 0 of 5 campus-flavoured unanswerable questions.

## Stage: embedding

Not retrieval, not the gate. `store.py::search` returns the nearest chunks and
`gate.py::check` compares a number to a number; both do exactly what they say.
The defect is in what those numbers mean.

`all-MiniLM-L6-v2` encodes what a passage is about. It does not encode whether a
passage answers a question, and nothing downstream can recover a distinction the
vector never carried.

## Evidence

```
  dist  answerable  overlap  question -> nearest document
 0.552       False        0  how much is tuition             -> admin_transcript_requests.txt
 0.699       False        0  what is the acceptance rate     -> admin_pass_fail_option.txt
 0.708       False        0  when is spring break            -> winter_gear.txt
 0.717       False        0  where is the football stadium   -> housing_fenwick_court.txt
 0.742       False        0  who is the university president -> admin_wifi_and_accounts.txt
 0.514        True        1  is it loud at night             -> housing_morrow_house_noise.txt
 0.631        True        1  how much walking is there       -> transit_walking.txt
 0.663        True        1  do I need a coat                -> winter_gear.txt
 0.680        True        1  where do people study           -> course_econ_101.txt
 0.706        True        0  what's the food like            -> dining_kestrel_commons.txt
```

Every unanswerable question shares **zero content words** with the document it
matched, and four of five still beat a question the corpus genuinely answers.

"How much is tuition" -> `admin_transcript_requests.txt` at 0.552. That document
says official transcripts cost $8. No shared word. The embedding matched a
shape: *official university service, has a price*. Correct, and not an answer.

"What's the food like" -> the document that genuinely answers it, at 0.706 —
**further away than the tuition non-answer**. Distance ordering is
anti-correlated with answerability in this sample.

## Why no threshold fixes it

```
mean pairwise distance between the 88 chunks of my own corpus = 0.774
  (min 0.114, max 1.141)
```

Every unanswerable question lands nearer to its best document (0.552-0.742) than
two random documents of the corpus are to each other (0.774). The cutoff of 0.75
is already below the corpus's own mean internal distance.

A single scalar is being asked to resolve a difference finer than the corpus's
own spread. Lower it and the vague-but-answerable go first (0.6 refused six of
ten real questions in unit 1). Raise it and everything passes. No value works,
because the populations overlap in the only dimension the gate can see.

## The pattern

One problem, not five. And it explains criterion 3's perfect score: the
OUT_OF_SCOPE questions differ from the corpus in both topic and register, so
they sit at 0.825-0.934 — above the corpus's own 0.774 mean. **Criterion 3 only
detects failures further away than my corpus is from itself.** Everything nearer
is invisible to it, and everything nearer is what a student would actually ask.

## Implication for Milestone 4

The signal isn't in the embedding, so the fix must ADD a signal rather than
re-tune one: check whether retrieved chunks contain what was asked about, not
whether they resemble it.

---

# Unit 2, Milestone 4 — the improvement

## What shipped

Hybrid search: a keyword signal alongside the vector one, used in the gate.
`gate.py::check` refuses when distance clears the cutoff **or** when no content
word of the question appears in any retrieved chunk
(`gate.py::has_lexical_support`). ~20 lines, plus passing `question` through
four `gate.check` call sites. Retrieval, chunking, index and prompt untouched.

Follows the diagnosis directly: the embedding carries no lexical signal, so add
one rather than re-tune the one that can't carry the distinction.

## What I tried first and rejected, with numbers

**BM25 proper.** `rank-bm25` ships with the starter and fusing a BM25 score with
the vector score is the obvious reading of "hybrid search". Built it, measured
before wiring:

```
ANSWERABLE vague      bm25 3.39 - 5.37
UNANSWERABLE campus   bm25 2.14 - 6.26
```

Ranges overlap completely. "When is spring break" scores 6.26 — higher than
every answerable question — because BM25 rewards term frequency and both
"spring" and "break" occur in unrelated senses. Weighted scoring measures how
*much* vocabulary overlaps, not whether the overlap means anything.

**Corpus-wide vocabulary check** (is the word anywhere in the 88 docs): strictly
weaker, 3 of 5 vs 4 of 5. "Acceptance rate" contains "rate", which exists in the
corpus but not in anything retrieved for that question.

**Distance margin** (best vs mean of top 5): answerable 0.020-0.266,
unanswerable 0.011-0.084. Total overlap.

**IDF thresholding**: "break" df=1, "walking" df=1. Identical rarity, opposite
answerability.

## Results

Every criterion identical before and after — all five were already MET, so on my
own criteria the change is invisible.

| | Before | After |
|---|---|---|
| Gate refuses campus-flavoured unanswerable | **0 of 5** | **4 of 5** |
| False refusals, my 5 test questions | 0 of 5 | 0 of 5 |
| False refusals, 5 vague real-phrasing | 0 of 5 | 0 of 5 |
| Criterion 3's own OUT_OF_SCOPE five | 5 of 5 | 5 of 5 |
| `how much is tuition` API cost | 1 call | **0 calls** |

Second-order effect: before, these reached the model and were refused by the
grounding instruction — correctly, 8 of 8 tested. The answer was already right;
what was wrong is that being right depended on the model obeying an instruction,
and cost a call each time.

## Attribution

Criteria 1, 3, 4 are deterministic, so before/after are exact comparisons not
samples. Only gate.py moved. Distances identical to three decimals in both logs.

## Still broken

"When is spring break" passes at 0.708. Both words exist in the corpus, "break"
in one document in an unrelated sense — lexical support that means nothing. The
check tests whether a connection exists, not whether it's meaningful. Deliberate:
requiring more than one matching word starts refusing real questions. One in five
is the price of zero false refusals.
