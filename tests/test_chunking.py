from app.rag.pipeline import split_into_chunks

def test_split_text_returns_chunks():
    chunks = split_into_chunks("A" * 2500, chunk_size=1000, overlap=100)
    assert len(chunks) == 3
    assert all(chunks)

def test_split_short_text():
    assert split_into_chunks("hello world") == ["hello world"]
