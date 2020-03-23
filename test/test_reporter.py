import logging
from pathlib import Path
from typing import List, Union
from unittest import TestCase, main

from reporter.constants import ERRORS
from reporter.newspaper_nlg_service import NewspaperNlgService

logging.disable(logging.CRITICAL)


class TestReporter(TestCase):
    def setUp(self):
        self.service = NewspaperNlgService()

    def _load_input_data(self, *files: str) -> str:
        data: List[str] = []
        for file in files:
            path = Path(__file__, "..", "resources", file).resolve()
            data.append(path.read_text())
        return "[{}]".format(", ".join(data))

    def _test_no_errors(self, file: Union[List[str], str], language: str, format: str):
        if isinstance(file, str):
            file = [file]
        data = self._load_input_data(*file)
        headline, body, head_err, body_err = self.service.run_pipeline(language, format, data)
        for error in ERRORS["en"].values():
            self.assertNotIn(error, headline)
            self.assertNotIn(error, body)
            self.assertIsNone(head_err)
            self.assertIsNone(body_err)

    def test_english_bigrams_report_does_not_error(self):
        self._test_no_errors("_extract_bigrams-1581332867317.json", "en", "p")

    def test_english_facets_report_does_not_error(self):
        self._test_no_errors("_extract_facets-1581332756287.json", "en", "p")

    def test_english_words_report_does_not_error(self):
        self._test_no_errors("_extract_words-1581332853353.json", "en", "p")

    def test_english_time_series_report_does_not_error(self):
        self._test_no_errors("_generate_time_series-1581332803610.json", "en", "p")

    def test_english_summaries_report_does_not_error(self):
        self._test_no_errors("summarization.json", "en", "p")

    def test_finnish_bigrams_report_does_not_error(self):
        self._test_no_errors("_extract_bigrams-1581332867317.json", "fi", "p")

    def test_finnish_facets_report_does_not_error(self):
        self._test_no_errors("_extract_facets-1581332756287.json", "fi", "p")

    def test_finnish_words_report_does_not_error(self):
        self._test_no_errors("_extract_words-1581332853353.json", "fi", "p")

    def test_finnish_time_series_report_does_not_error(self):
        self._test_no_errors("_generate_time_series-1581332803610.json", "fi", "p")

    def test_finnish_summaries_report_does_not_error(self):
        self._test_no_errors("summarization.json", "fi", "p")

    def test_output_format_ol_does_not_error(self):
        self._test_no_errors("_generate_time_series-1581332803610.json", "fi", "ol")

    def test_output_format_ul_does_not_error(self):
        self._test_no_errors("_generate_time_series-1581332803610.json", "fi", "ul")

    def test_output_multiple_inputs_does_not_error(self):
        self._test_no_errors(
            ["_generate_time_series-1581332803610.json", "_extract_facets-1581332756287.json"], "fi", "ul"
        )


if __name__ == "__main__":
    main()
