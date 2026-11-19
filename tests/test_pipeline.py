import unittest

from core.chunk import split_text_into_chunks
from core.multilingual import detect_language, translate_to_english


class TestPipeline(unittest.TestCase):
    def test_split_text_into_chunks(self):
        text = "one two three four five six seven eight nine ten"
        chunks = split_text_into_chunks(text, chunk_size=4, overlap=1)
        self.assertEqual(chunks, [
            "one two three four",
            "four five six seven",
            "seven eight nine ten",
        ])

    def test_detect_language(self):
        self.assertEqual(detect_language("This is a test case."), "en")
        self.assertEqual(detect_language("यह एक परीक्षण है।"), "hi")

    def test_translate_to_english_returns_english_text(self):
        english = "This is already English."
        self.assertEqual(translate_to_english(english, source_lang="en"), english)


if __name__ == "__main__":
    unittest.main()
