import logging
from typing import List, Type

from reporter.core.models import Fact, Message
from reporter.core.realize_slots import SlotRealizerComponent
from reporter.newspaper_message_generator import TaskResult
from reporter.resources.processor_resource import ProcessorResource

log = logging.getLogger("root")


TEMPLATE = """
en: {result_value} relevant articles were found in issues of {result_key} published during the year {timestamp_from}
fi: löydettiin {result_value} relevanttia artikkelia jotka oli julkaistu {result_key, case=ssa} vuoden {timestamp_from} aikana
| analysis_type = GenerateTimeSeries:absolute_counts

en: between {timestamp_from} and {timestamp_to}, the largest yearly amount of relevant articles in {result_key} was {result_value}
fi: vuosien {timestamp_from} ja {timestamp_to} välillä, suurin vuosittainen määrä relevantteja artikkeleita {result_key, case=ssa} oli {result_value}
| analysis_type = GenerateTimeSeries:absolute_counts:max

en: between {timestamp_from} and {timestamp_to}, the smallest non-zero yearly amount of relevant articles in {result_key} was {result_value}
fi: vuosien {timestamp_from} ja {timestamp_to} välillä, pienin nollasta eroava määrä relevantteja artikkeleita {result_key, case=ssa} oli {result_value}
| analysis_type = GenerateTimeSeries:absolute_counts:min

en: between {timestamp_from} and {timestamp_to}, the average amount of relevant articles in {result_key} was {result_value}
fi: vuosien {timestamp_from} ja {timestamp_to} välillä, {result_key, case=ssa} julkaistiin vuosittain keskimäärin {result_value} relevanttia artikkelia
| analysis_type = GenerateTimeSeries:absolute_counts:avg
"""  # noqa: E501


class GenerateTimeSeriesResource(ProcessorResource):
    def templates_string(self) -> str:
        return TEMPLATE

    def parse_messages(self, task_result: TaskResult, context: List[TaskResult]) -> List[Message]:
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
                                    "during_year",  # timestamp_type
                                    "GenerateTimeSeries:" + value_type,  # analysis_type
                                    "[ENTITY:{}:{}]".format(facet_name, facet_value),  # result_key
                                    value,  # result_value
                                    interestingness,  # outlierness
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
                                )
                            ]
                        )
                    )
        return messages

    def slot_realizer_components(self) -> List[Type[SlotRealizerComponent]]:
        return []
