from reporter.resources.processor_resource import ProcessorResource

TEMPLATE = """
en: {timestamp_from}, the number of entries {result_key} {result_value}
en: the number of entries {result_key} {result_value} {timestamp_from}
fi: {timestamp_from}, {result_key} tulosten lukumäärä {result_value}
de: die Anzahl der Einträge {result_key} {result_value} {timestamp_from}
| analysis_type = step_detection
"""


class StepDetectionResource(ProcessorResource):
    def templates_string(self) -> str:
        return TEMPLATE
