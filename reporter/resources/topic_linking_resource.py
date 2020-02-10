from reporter.resources.processor_resource import ProcessorResource

TEMPLATE = """
en: the queried documents have distance {result_value} to {result_key}
fi: kyselyyn käytetyillä dokumenteilla on etäisyys {result_value} {result_key}
de: die abgefragten Dokumente haben den Abstand {result_value} zu {result_key}
| analysis_type = tm_document_distance
"""


class TopicLinkingResource(ProcessorResource):
    def templates_string(self) -> str:
        return TEMPLATE
