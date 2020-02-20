import logging
from typing import List, Type

from reporter.core.models import Fact, Message
from reporter.core.realize_slots import RegexRealizer, SlotRealizerComponent
from reporter.newspaper_message_generator import TaskResult
from reporter.resources.processor_resource import ProcessorResource

log = logging.getLogger("root")


TEMPLATE = """
en: the search found {result_value} articles published during {result_key}
fi: haussa löytyi {result_value} artikkelia jotka oli julkaistu vuonna {result_key}
| analysis_type = ExtractFacets:PUB_YEAR

en: the search found {result_value} articles in {result_key}
fi: löydettiin {result_value} artikkelia joiden kieli oli {result_key}
| analysis_type = ExtractFacets:LANGUAGE

en: the search found {result_value} articles from the newspaper {result_key}
fi: löydettiin {result_value} artikkelia jotka oli julkaistu {result_key, case=ssa}
| analysis_type = ExtractFacets:NEWSPAPER_NAME
"""


class ExtractFacetsResource(ProcessorResource):
    def templates_string(self) -> str:
        return TEMPLATE

    def parse_messages(self, task_result: TaskResult, context: List[TaskResult]) -> List[Message]:
        if not task_result.processor == "ExtractFacets":
            return []

        corpus, corpus_type = self.build_corpus_fields(task_result)

        messages = []
        for facet_name, results in task_result.task_result["result"].items():
            interestingness_values = task_result.task_result["interestingness"][facet_name]
            for facet_value, result_value in results.items():
                interestingness = interestingness_values[facet_value]

                # In cases where we have a *ton* of different values (e.g. issues from

                messages.append(
                    Message(
                        [
                            Fact(
                                corpus,  # corpus
                                corpus_type,  # corpus_type
                                None,  # timestamp_from
                                None,  # timestamp_to
                                "all_time",  # timestamp_type
                                "ExtractFacets:" + facet_name,  # analysis_type
                                "[{}:{}]".format(facet_name, facet_value),  # result_key
                                result_value,  # result_value
                                interestingness,  # interestingness
                            )
                        ]
                    )
                )
        return messages

    def slot_realizer_components(self) -> List[Type[SlotRealizerComponent]]:
        return [PubYearRealizer, NewsPaperNameRealizer, LanguageRealizer]


class PubYearRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "ANY", r"\[PUB_YEAR:([^\]]+)\]", 1, "{}")


class LanguageRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "ANY", r"\[LANGUAGE:([^\]]+)\]", 1, "[ENTITY:LANGUAGE:{}]")


class NewsPaperNameRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "ANY", r"\[NEWSPAPER_NAME:([^\]]+)\]", 1, "[ENTITY:NEWSPAPER:{}]")
