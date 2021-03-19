import logging
from typing import List, Type

from reporter.core.models import Fact, Message
from reporter.core.realize_slots import SlotRealizerComponent, RegexRealizer
from reporter.newspaper_message_generator import TaskResult
from reporter.resources.processor_resource import ProcessorResource

log = logging.getLogger("root")


TEMPLATE = """
en: {result_value} relevant articles were found in issues of {result_key} published during {time} {analysis_id}
fi: löydettiin {result_value} relevanttia artikkelia jotka oli julkaistu {result_key} -lehdessä {time} aikana {analysis_id}
de: {result_value} relevante Artikel wurde in Ausgaben von {result_key} gefunden, die im {time} publiziert wurden {analysis_id}
fr: {result_value} articles correspondant à votre recherche ont été trouvés dans les numéros du {result_key} publiés au cours de {time} {analysis_id}
| analysis_type = GenerateTimeSeries:absolute_counts

en: {time} the largest yearly amount of relevant articles in {result_key} was {result_value} {analysis_id}
fi: {time} suurin vuosittainen määrä relevantteja artikkeleita {result_key} -lehdessä oli {result_value} {analysis_id}
de: {time} waren {result_value} Artikel die größte jährliche Menge von relevanten Artikeln in {result_key} {analysis_id}
fr: Le plus grand nombre d'articles correspondant à votre recherche dans le {result_key} {time} est {result_value} articles sur une année {analysis_id}
| analysis_type = GenerateTimeSeries:absolute_counts:max

en: {time} the smallest non-zero yearly amount of relevant articles in {result_key} was {result_value} {analysis_id}
fi: {time} pienin nollasta eroava määrä relevantteja artikkeleita {result_key} -lehdessä oli {result_value} {analysis_id}
de: {time} war {result_value} die kleinste jährliche Nicht-Null-Anzahl von relevanten Artikeln, die in {result_key} publiziert wurden {analysis_id}
fr: le plus petit montant supérieur à 0 d’articles correspondant à votre recherche dans le {result_key} {time} est de {result_value} {analysis_id}
| analysis_type = GenerateTimeSeries:absolute_counts:min

en: {time} the average amount of relevant articles in {result_key} was {result_value} {analysis_id}
fi: {time} {result_key} -lehdessä julkaistiin vuosittain keskimäärin {result_value} relevanttia artikkelia {analysis_id}
de: {time} war {result_value} die durchschnittliche Menge von relevanten Artikeln in {result_key} {analysis_id}
fr: le nombre moyen d'articles correspondant à votre recherche dans {result_key} {time} est de {result_value} {analysis_id}
| analysis_type = GenerateTimeSeries:absolute_counts:avg
"""  # noqa: E501


class GenerateTimeSeriesResource(ProcessorResource):
    def templates_string(self) -> str:
        return TEMPLATE

    def parse_messages(self, task_result: TaskResult, context: List[TaskResult], language: str) -> List[Message]:
        if not task_result.processor == "GenerateTimeSeries":
            return []

        messages = []
        for parser in [self.parse_standard_messages, self.parse_complex_messages]:
            messages.extend(parser(task_result, context))

        return messages

    def parse_standard_messages(self, task_result: TaskResult, context: List[TaskResult]) -> List[Message]:
        corpus, corpus_type = self.build_corpus_fields(task_result)
        messages = []

        facet_name = task_result.parameters["facet_name"]
        for value_type, value_type_results in task_result.task_result["result"].items():
            if value_type != "absolute_counts":
                continue  # TODO: relative_counts are not percentages and are thus really hard to talk about.
            for facet_value, facet_value_results in value_type_results.items():
                for time, value in facet_value_results.items():
                    interestingness = task_result.task_result["interestingness"][facet_value][1].get(
                        time, ProcessorResource.EPSILON
                    )

                    if not time.isnumeric():
                        continue

                    if interestingness == 0:
                        continue

                    messages.append(
                        Message(
                            [
                                Fact(
                                    corpus,  # corpus
                                    corpus_type,  # corpus_type
                                    time,  # timestamp_from
                                    time,  # timestamp_to
                                    "year",  # timestamp_type
                                    "GenerateTimeSeries:" + value_type,  # analysis_type
                                    "[ENTITY:{}:{}]".format(facet_name, facet_value),  # result_key
                                    value,  # result_value
                                    interestingness,  # outlierness
                                    "[LINK:{}]".format(task_result.uuid),  # uuid
                                )
                            ]
                        )
                    )
        return messages

    def parse_complex_messages(self, task_result: TaskResult, context: List[TaskResult]) -> List[Message]:
        corpus, corpus_type = self.build_corpus_fields(task_result)
        messages = []

        facet_name = task_result.parameters["facet_name"]
        for value_type, value_type_results in task_result.task_result["result"].items():
            if value_type != "absolute_counts":
                continue  # TODO: relative_counts are not percentages and are thus really hard to talk about.
            for facet_value, facet_value_results in value_type_results.items():
                from_year = str(min([int(y) for y in facet_value_results.keys() if y.isnumeric()]))
                to_year = str(max([int(y) for y in facet_value_results.keys() if y.isnumeric()]))
                for complex_key in ["max", "min", "avg"]:
                    value = facet_value_results[complex_key]
                    interestingness = task_result.task_result["interestingness"][facet_value][0]
                    messages.append(
                        Message(
                            [
                                Fact(
                                    corpus,  # corpus
                                    corpus_type,  # corpus_type
                                    from_year,  # timestamp_from
                                    to_year,  # timestamp_to
                                    "between_years",  # timestamp_type
                                    "GenerateTimeSeries:{}:{}".format(value_type, complex_key),  # analysis_type
                                    "[ENTITY:{}:{}]".format(facet_name, facet_value),  # result_key
                                    value,  # result_value
                                    interestingness,  # outlierness
                                    "[LINK:{}]".format(task_result.uuid),  # uuid
                                )
                            ]
                        )
                    )
        return messages

    def slot_realizer_components(self) -> List[Type[SlotRealizerComponent]]:
        return [NewsPaperNameRealizer]


class NewsPaperNameRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "ANY", r"\[ENTITY:NEWSPAPER_NAME:([^\]]+)\]", 1, "[ENTITY:NEWSPAPER:{}]")
