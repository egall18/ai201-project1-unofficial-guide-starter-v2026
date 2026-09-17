"""
Stage 2 of the pipeline: splitting documents into chunks.

⚠️ THIS IS THE FILE YOU CHANGE IN MILESTONE 3.

`split_documents` below is deliberately plain. It cuts every document into
fixed-size pieces with a fixed overlap and pays no attention to where sentences
or paragraphs end. It works, and it is not good.

On a corpus of short posts it may not cut anything at all: `campus_life` comes
out as 88 documents and 88 chunks, because almost nothing in it reaches 800
characters. That is the baseline, not a bug — Milestone 3 is where you decide
whether one post should stay one chunk.

Your job in Milestone 3 is to replace the *body* of `split_documents` with a
strategy that fits the documents you actually read in Milestone 1. Keep the
name and the shape of what it returns — the rest of the pipeline calls it, and
your README has to name the function that produced your chunks.

If you get stuck for 30 minutes, `fallback_split` is the original. Switch back
to it, write down what you saw, and move on. That's a real observation about
your pipeline, not giving up.
"""

import re
from dataclasses import dataclass

import config
from ingest import Document


@dataclass
class Chunk:
    """One piece of one document."""

    text: str
    source: str        # which file it came from
    index: int         # which chunk within that file, starting at 0
    produced_by: str   # the function that made it — cite this in your README

    @property
    def label(self) -> str:
        return f"{self.source}#{self.index}"


def fallback_split(
    documents: list[Document],
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[Chunk]:
    """
    The starter's original chunker. Fixed-size character windows with overlap.

    Keep this function. Milestone 3's stop rule points back at it, and having
    something to compare your own strategy against is useful in unit 2.
    """
    chunk_size = chunk_size or config.CHUNK_SIZE
    overlap = overlap or config.CHUNK_OVERLAP

    if overlap >= chunk_size:
        raise ValueError("overlap has to be smaller than chunk_size")

    chunks: list[Chunk] = []
    for doc in documents:
        start = 0
        index = 0
        while start < len(doc.text):
            piece = doc.text[start : start + chunk_size].strip()
            if piece:
                chunks.append(
                    Chunk(
                        text=piece,
                        source=doc.source,
                        index=index,
                        produced_by="chunker.py::fallback_split",
                    )
                )
                index += 1
            start += chunk_size - overlap

    return chunks


_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def _split_long_paragraph(paragraph: str, budget: int) -> list[str]:
    """
    Break one oversized paragraph on sentence boundaries.

    Nothing in campus_life needs this — the longest paragraph is 373 characters
    against a budget of roughly 570 — but a chunker that quietly cuts a sentence
    in half the first time it meets a long document isn't worth trusting.
    """
    pieces: list[str] = []
    current = ""
    for sentence in _SENTENCE_END.split(paragraph):
        if current and len(current) + 1 + len(sentence) > budget:
            pieces.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        pieces.append(current)
    return pieces


def split_documents(documents: list[Document]) -> list[Chunk]:
    """
    Paragraph-aware chunking that keeps every chunk under its own title.

    Three rules, each of which comes from something in campus_life:

    1. **Never cut inside a paragraph.** Documents here are 178 to 549
       characters of somebody's advice, in 2 to 5 short paragraphs. The median
       paragraph is 93 characters, so paragraphs are the smallest piece that
       still says something — "Best time to do laundry here is Tuesday or
       Wednesday morning" is a fact only if you know which building.

    2. **Every chunk carries the document's title line.** That line is the only
       thing separating seven near-identical laundry files from each other, and
       it appears exactly once, at the top. A chunk that loses it still
       retrieves for a laundry question and still reads like an answer, which
       is worse than not retrieving at all. Acceptance criterion 4 is this rule.

    3. **A document that fits stays whole.** At CHUNK_SIZE 600 every campus_life
       document does, so one post is one chunk — a decision, not an accident.
       Each document is one person writing about one thing; splitting it would
       manufacture the near-duplicates I'm already fighting in retrieval.

    Compare `fallback_split`, which slices on a character count and pays no
    attention to any of this. On advice_threads it emits three trailing chunks
    that are strict suffixes of the chunk before them, one of them two
    characters long, none carrying a title.
    """
    chunk_size = config.CHUNK_SIZE
    overlap = config.CHUNK_OVERLAP

    if overlap >= chunk_size:
        raise ValueError("overlap has to be smaller than chunk_size")

    chunks: list[Chunk] = []

    for doc in documents:
        head, _, body = doc.text.strip().partition("\n")
        title = head.strip()

        paragraphs: list[str] = []
        for block in body.split("\n\n"):
            block = block.strip()
            if not block:
                continue
            # Leave room for the title that gets prepended to every chunk.
            budget = max(chunk_size - len(title) - 2, chunk_size // 2)
            if len(block) > budget:
                paragraphs.extend(_split_long_paragraph(block, budget))
            else:
                paragraphs.append(block)

        if not paragraphs:
            chunks.append(
                Chunk(
                    text=title,
                    source=doc.source,
                    index=0,
                    produced_by="chunker.py::split_documents",
                )
            )
            continue

        budget = max(chunk_size - len(title) - 2, chunk_size // 2)
        groups: list[list[str]] = []
        current: list[str] = []
        for paragraph in paragraphs:
            projected = len("\n\n".join(current + [paragraph]))
            if current and projected > budget:
                groups.append(current)
                # Overlap, measured in whole paragraphs rather than characters:
                # carry the last one forward only if it fits the allowance.
                tail = current[-1]
                current = [tail] if 0 < len(tail) <= overlap else []
            current.append(paragraph)
        if current:
            groups.append(current)

        for index, group in enumerate(groups):
            chunks.append(
                Chunk(
                    text=f"{title}\n\n" + "\n\n".join(group),
                    source=doc.source,
                    index=index,
                    produced_by="chunker.py::split_documents",
                )
            )

    return chunks


def describe(chunks: list[Chunk]) -> str:
    """A one-line summary, printed after indexing."""
    if not chunks:
        return "0 chunks"
    lengths = [len(c.text) for c in chunks]
    return (
        f"{len(chunks)} chunks, "
        f"{sum(lengths) // len(lengths)} characters on average "
        f"(shortest {min(lengths)}, longest {max(lengths)}), "
        f"produced by {chunks[0].produced_by}"
    )


if __name__ == "__main__":
    from ingest import load_documents

    chunks = split_documents(load_documents())
    print(describe(chunks))
