from reporter.resources.processor_resource import ProcessorResource

TEMPLATE = """
${anyquery}: query, query_minmatches, query_minmatches_filter, filter, query_filter

en-head: Analysis of a corpus defined by {corpus}
fi-head: Analyysi korpuksesta kyselyllä {corpus}
de-head: Analyse mit der Abfrage {corpus}
| corpus_type in {anyquery}

en-head: Analysis of the complete corpus
fi-head: Analyysi koko korpuksesta
de-head: Analyse des gesamten Korpus
| corpus_type = full_corpus
"""


class NewspaperCorpusResource(ProcessorResource):
    def templates_string(self) -> str:
        return TEMPLATE
