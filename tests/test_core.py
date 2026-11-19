from core.chunk import split_text_into_chunks


def test_split_text_into_chunks():
    text = "one two three four five six seven eight nine ten"
    chunks = split_text_into_chunks(text, chunk_size=4, overlap=1)
    assert chunks == [
        "one two three four",
        "four five six seven",
        "seven eight nine ten",
    ]
