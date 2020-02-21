import logging
from pathlib import Path
from typing import List
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

    def test_english_bigrams_report_does_not_error(self):
        data = self._load_input_data("_extract_bigrams-1581332867317.json")
        headline, body = self.service.run_pipeline("en", "p", data)
        for error in ERRORS["en"].values():
            self.assertNotIn(error, headline)
            self.assertNotIn(error, body)

    def test_english_facets_report_does_not_error(self):
        data = self._load_input_data("_extract_facets-1581332756287.json")
        headline, body = self.service.run_pipeline("en", "p", data)
        for error in ERRORS["en"].values():
            self.assertNotIn(error, headline)
            self.assertNotIn(error, body)

    def test_english_words_report_does_not_error(self):
        data = self._load_input_data("_extract_words-1581332853353.json")
        headline, body = self.service.run_pipeline("en", "p", data)
        for error in ERRORS["en"].values():
            self.assertNotIn(error, headline)
            self.assertNotIn(error, body)

    def test_english_time_series_report_does_not_error(self):
        data = self._load_input_data("_generate_time_series-1581332803610.json")
        headline, body = self.service.run_pipeline("en", "p", data)
        for error in ERRORS["en"].values():
            self.assertNotIn(error, headline)
            self.assertNotIn(error, body)

    def test_finnish_bigrams_report_does_not_error(self):
        data = self._load_input_data("_extract_bigrams-1581332867317.json")
        headline, body = self.service.run_pipeline("fi", "p", data)
        for error in ERRORS["en"].values():
            self.assertNotIn(error, headline)
            self.assertNotIn(error, body)

    def test_finnish_facets_report_does_not_error(self):
        data = self._load_input_data("_extract_facets-1581332756287.json")
        headline, body = self.service.run_pipeline("fi", "p", data)
        for error in ERRORS["en"].values():
            self.assertNotIn(error, headline)
            self.assertNotIn(error, body)

    def test_finnish_words_report_does_not_error(self):
        data = self._load_input_data("_extract_words-1581332853353.json")
        headline, body = self.service.run_pipeline("fi", "p", data)
        for error in ERRORS["en"].values():
            self.assertNotIn(error, headline)
            self.assertNotIn(error, body)

    def test_finnish_time_series_report_does_not_error(self):
        data = self._load_input_data("_generate_time_series-1581332803610.json")
        headline, body = self.service.run_pipeline("fi", "p", data)
        for error in ERRORS["en"].values():
            self.assertNotIn(error, headline)
            self.assertNotIn(error, body)

    def test_output_format_ol_does_not_error(self):
        data = self._load_input_data("_generate_time_series-1581332803610.json")
        headline, body = self.service.run_pipeline("fi", "ol", data)
        for error in ERRORS["en"].values():
            self.assertNotIn(error, headline)
            self.assertNotIn(error, body)

    def test_output_format_ul_does_not_error(self):
        data = self._load_input_data("_generate_time_series-1581332803610.json")
        headline, body = self.service.run_pipeline("fi", "ul", data)
        for error in ERRORS["en"].values():
            self.assertNotIn(error, headline)
            self.assertNotIn(error, body)

    def test_output_multiple_inputs_does_not_error(self):
        data = self._load_input_data("_generate_time_series-1581332803610.json", "_extract_facets-1581332756287.json")
        headline, body = self.service.run_pipeline("fi", "ul", data)
        for error in ERRORS["en"].values():
            self.assertNotIn(error, headline)
            self.assertNotIn(error, body)


if __name__ == "__main__":
    main()
