from reporter.resources.processor_resource import ProcessorResource

TEMPLATE = """
en: there were {result_value} entries related to {result_key}
fi: löydettiin {result_value} {result_key} tulosta
de: es gibt {result_value} Einträge zu {result_key}
| analysis_type = topic_count

en: {result_key} appeared {result_value} times
fi: {result_key} löytyi {result_value} kertaa
de: {result_key} wurde {result_value} mal gefunden
| analysis_type = word_count

en: {result_key} had a relative frequency of {result_value} instances per million words
fi: {result_key} suhteellinen esiitymistiheys oli {result_value} esiintymää miljoonaa sanaa kohti
de: {result_key} hat eine relative Häufigkeit von {result_value} Instanzen pro Million Wörter
| analysis_type = word_ipm

en: {result_key} had a TF-IDF value of {result_value}
fi: {result_key} TF-IDF arvo oli {result_value}
de: {result_key} hat einen TF-IDF-Wert von {result_value}
| analysis_type = word_tfidf
"""


class WordStatisticsResource(ProcessorResource):
    def templates_string(self) -> str:
        return TEMPLATE
