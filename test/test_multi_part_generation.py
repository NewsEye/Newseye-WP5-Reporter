import logging
from pathlib import Path
from unittest import TestCase, main

from reporter.newspaper_nlg_service import NewspaperNlgService

logging.disable(logging.CRITICAL)


class TestMultiPartGeneration(TestCase):
    def setUp(self):
        self.service = NewspaperNlgService()

    def _load_input_data(self, file: str) -> str:
        return Path(__file__, "..", "resources", file).resolve().read_text()

    def _test_has_parts(self, file: str, language: str, format: str, part_count: int):
        data = self._load_input_data(file)
        headline, body, errors = self.service.run_pipeline(language, format, data)

        self.assertListEqual(errors, [])

        if part_count == 1:
            self.assertFalse(isinstance(headline, list))
            self.assertFalse(isinstance(body, list))
        else:
            self.assertEqual(len(headline), part_count)
            self.assertEqual(len(body), part_count)

    def test_multipart_dataset(self):
        self._test_has_parts("_multi_dataset.json", "en", "p", 2)

    def test_multipart_query(self):
        self._test_has_parts("_multi_query.json", "en", "p", 2)


if __name__ == "__main__":
    main()
