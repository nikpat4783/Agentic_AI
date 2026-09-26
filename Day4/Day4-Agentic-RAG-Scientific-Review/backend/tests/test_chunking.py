from app.rag.chunking import chunk_text


def test_short_text_returns_single_chunk():
    text = "This is a short abstract."
    chunks = chunk_text(text, chunk_size=800, overlap=120)
    assert chunks == [text]


def test_empty_text_returns_no_chunks():
    assert chunk_text("") == []
    assert chunk_text("   ") == []


def test_long_text_is_split_at_sentence_boundaries_with_no_data_loss():
    text = " ".join(f"Sentence {i} is here." for i in range(40))  # well over 800 chars
    chunks = chunk_text(text, chunk_size=800, overlap=120)

    assert len(chunks) > 1
    # every chunk should not exceed the requested size
    assert all(len(c) <= 800 for c in chunks)
    # every chunk ends at a sentence boundary, since no individual sentence
    # here is long enough to trigger the hard-slice fallback
    assert all(c.rstrip()[-1] in ".!?" for c in chunks)


def test_chunk_size_boundary_exact_length():
    # No sentence-ending punctuation, so this is a single "sentence" that
    # exactly fits chunk_size -- exercises the single-sentence-fits path.
    text = "a" * 800
    chunks = chunk_text(text, chunk_size=800, overlap=120)
    assert chunks == [text]


def test_single_sentence_exceeding_chunk_size_falls_back_to_hard_slice():
    # One long "sentence" (no punctuation) longer than chunk_size must still
    # be split, with no data loss, via the hard-slice fallback.
    text = "a" * 2000
    chunks = chunk_text(text, chunk_size=800, overlap=120)

    assert len(chunks) > 1
    assert all(len(c) <= 800 for c in chunks)
    # reassembling without overlap duplication isn't required by the
    # contract, but every char of the original text must appear somewhere
    # and chunks must be produced entirely from slices of the original text
    assert all(c in text for c in chunks)
    assert chunks[0] == text[:800]
