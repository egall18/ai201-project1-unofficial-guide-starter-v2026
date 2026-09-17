"""
Settings for The Unofficial Guide.

Everything you're likely to change lives here, at the top, on purpose.
You'll edit THRESHOLD in Milestone 4 and the chunking numbers in Milestone 3.

Anything you set in your .env file wins over the defaults here.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")


# ─── The corpus you're working with ──────────────────────────────────────────
# Change this to switch corpora, or pass --corpus on the command line.
# Options are the folder names inside corpora/. See corpora/README.md.

CORPUS = os.getenv("AI201_CORPUS", "campus_life")


# ─── Chunking (Milestone 3) ──────────────────────────────────────────────────
# These are deliberately plain, generic numbers. Milestone 3 is where you
# replace them with numbers that fit the documents you actually read.

# Measured before choosing: campus_life is 88 documents of 178-549 characters,
# 2-5 paragraphs each, median paragraph 93 characters.
#
# 600 sits just above the longest document (549). That makes "one post, one
# chunk" an explicit decision with 51 characters of margin, rather than
# something that happened to be true because the default was 800. Anything
# smaller starts splitting posts that are already one person's single thought.
CHUNK_SIZE = 600

# Zero, because split_documents never cuts inside a paragraph and prepends the
# document's title line to every chunk. Overlap exists to stop a sentence
# sliced down the middle from being unreadable; nothing here gets sliced, so
# overlap would only copy text into the index twice — and near-duplicate chunks
# are the exact problem this corpus already has too much of.
CHUNK_OVERLAP = 0


# ─── Retrieval (Milestone 4) ─────────────────────────────────────────────────

TOP_K = 5               # how many chunks to pull back per question

# The relevance gate. If the best chunk is further away than this, the system
# refuses to answer instead of handing the model thin material.
#
# LOWER IS BETTER: 0.3 is a close match, 0.9 is unrelated.
#
# Measured in Milestone 4, not guessed.
#
#   my 5 test questions        0.215 - 0.412
#   the 5 OUT_OF_SCOPE ones    0.825 - 0.934
#
# That gap is enormous, and 0.6 sits in the middle of it — but 0.6 is wrong
# anyway, and the curated questions are why it looks right. Ten vaguer
# questions this corpus genuinely answers ("what's the food like", "do I need a
# coat", "where do people study") run 0.408 to 0.706, so a 0.6 cutoff refuses
# six of them. My own test questions are phrased by someone who already knew the
# answer; real ones aren't.
#
# 0.75 sits above that 0.706 ceiling and below the 0.825 floor of the
# out-of-scope group, so it admits the vague-but-answerable and still refuses
# all five out-of-scope questions.
#
# What this does NOT fix: campus-flavoured questions the corpus can't answer
# land at 0.552 ("how much is tuition") through 0.742 ("who is the university
# president"), straight through the in-corpus range. No threshold separates
# those — see gate.py, which says it: the gate catches the clear misses and the
# prompt catches the near ones. This number is set for the first job only.
THRESHOLD = 0.75


# ─── Models ──────────────────────────────────────────────────────────────────
# Embeddings run on your own machine and cost no API quota.
# Only generation calls out to a service.

# This is the model Chroma bundles, and leaving it alone is the fast path: it
# downloads about 80 MB from Chroma's own CDN and needs nothing else installed.
#
# Setting it to any other name — unit 2's "try a second embedding model"
# stretch option — switches to loading that model from Hugging Face instead,
# which needs `pip install 'sentence-transformers>=3.4,<3.5'` first. store.py
# says so with a real error message rather than a stack trace if you forget.
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
MODEL = os.getenv("AI201_MODEL", "gemini-3.5-flash-lite")


# ─── Rate limiting and quota guards ──────────────────────────────────────────
# You should not need to touch these. They exist so that a runaway loop costs
# you a warning instead of your whole day's allowance.

REQUESTS_PER_MINUTE = 30       # outgoing calls the limiter will allow per minute
SESSION_REQUEST_BUDGET = 300   # stop and warn rather than draining the daily quota
MAX_RETRIES = 4                # on 429 / resource-exhausted, with backoff

CACHE_ENABLED = os.getenv("AI201_CACHE", "1") != "0"
CACHE_DIR = ROOT / ".cache"


# ─── Paths ───────────────────────────────────────────────────────────────────

CORPORA_DIR = ROOT / "corpora"
CHROMA_DIR = ROOT / "chroma_db"
RESULTS_DIR = ROOT / "results"


def corpus_path(name: str | None = None) -> Path:
    """Folder holding the documents for a corpus."""
    return CORPORA_DIR / (name or CORPUS) / "documents"


def collection_name(name: str | None = None, variant: str = "default") -> str:
    """
    Name of the vector-store collection for a corpus.

    `variant` lets you index the same corpus two different ways and query both
    without deleting anything — you'll want that in unit 2 when you compare
    chunking strategies.

    Chroma is fussy about collection names: 3 to 63 characters, starting and
    ending with a letter or digit, and nothing but letters, digits, underscores
    and hyphens in between. If you bring your own corpus and name the folder
    something Chroma won't accept, this cleans it up rather than failing.
    """
    import re

    raw = f"{name or CORPUS}__{variant}"
    cleaned = re.sub(r"[^A-Za-z0-9_-]", "-", raw)
    cleaned = cleaned.strip("_-")          # must start and end alphanumeric
    if not cleaned or not cleaned[0].isalnum():
        cleaned = f"c{cleaned}"
    if not cleaned[-1].isalnum():
        cleaned = f"{cleaned}0"
    return cleaned[:63].rstrip("_-") or "collection"
