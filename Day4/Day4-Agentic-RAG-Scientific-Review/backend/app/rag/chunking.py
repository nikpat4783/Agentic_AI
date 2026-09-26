import re


def _split_sentences(text: str) -> list[str]:
    return [s for s in re.split(r"(?<=[.!?])\s+", text) if s]


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 120) -> list[str]:
    """Sentence-aware splitter with overlap. Abstracts are short
    (~150-300 words), so most inputs produce 1-2 chunks.

    Sentences are greedily packed into chunks up to `chunk_size` chars. When a
    chunk fills up, trailing sentences from its end (up to `overlap` chars)
    are carried over to seed the next chunk, so consecutive chunks overlap at
    a sentence boundary rather than a hard character cut. A single sentence
    longer than `chunk_size` is hard-sliced (same as the old behavior) since
    there's no smaller boundary to split on.
    """
    text = text.strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    sentences = _split_sentences(text)

    chunks = []
    current: list[str] = []
    current_len = 0

    def flush():
        if current:
            chunks.append(" ".join(current).strip())

    for sentence in sentences:
        if len(sentence) > chunk_size:
            # Flush whatever we've accumulated so far, then hard-slice this
            # oversized sentence on its own (no smaller boundary available).
            flush()
            current = []
            current_len = 0
            start = 0
            while start < len(sentence):
                end = min(start + chunk_size, len(sentence))
                chunks.append(sentence[start:end].strip())
                if end == len(sentence):
                    break
                start = end - overlap
            continue

        extra = (1 if current else 0) + len(sentence)
        if current and current_len + extra > chunk_size:
            flush()
            # Carry over trailing sentences (up to `overlap` chars) from the
            # chunk we just closed, so the new chunk overlaps at a sentence
            # boundary.
            carried: list[str] = []
            carried_len = 0
            for prev_sentence in reversed(current):
                added = (1 if carried else 0) + len(prev_sentence)
                if carried_len + added > overlap:
                    break
                carried.insert(0, prev_sentence)
                carried_len += added
            current = carried
            current_len = carried_len

        if current:
            current_len += 1 + len(sentence)
        else:
            current_len = len(sentence)
        current.append(sentence)

    flush()
    return [c for c in chunks if c]
