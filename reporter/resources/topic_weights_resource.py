from reporter.resources.processor_resource import ProcessorResource

TEMPLATE = """
en: the corpus defined by {corpus} is associated with {result_key} with weight {result_value}
fi: kysely {corpus} liittyy {result_key} painoarvolla {result_value}
de: der Korpus definiert mit {corpus} ist mit {result_key} mit Gewicht {result_value} verbunden
| analysis_type = topic_weight
"""


class TopicWeightsResource(ProcessorResource):
    def templates_string(self) -> str:
        return TEMPLATE
