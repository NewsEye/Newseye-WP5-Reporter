import logging
from typing import List, Type

from reporter.core.models import Fact, Message
from reporter.core.realize_slots import RegexRealizer, SlotRealizerComponent
from reporter.newspaper_message_generator import TaskResult
from reporter.resources.processor_resource import ProcessorResource

log = logging.getLogger("root")


TEMPLATE = """
en: {result_key} appeared {result_value} times
fi: {result_key} esiintyi {result_value} kertaa
| analysis_type = ExtractWords:Count

en: {result_key} had a relative count of {result_value}
fi: {result_key, case=gen} suhteellinen osuus oli {result_value}
| analysis_type = ExtractWords:RelativeCount

en: {result_key} had a TF-IDF score of {result_value}
fi: {result_key, case=gen} TF-IDF -luku oli {result_value}
| analysis_type = ExtractWords:TFIDF
"""


class ExtractWordsResource(ProcessorResource):
    def templates_string(self) -> str:
        return TEMPLATE

    def parse_messages(self, task_result: TaskResult, context: List[TaskResult]) -> List[Message]:
        if not task_result.processor == "ExtractWords":
            return []

        unit: str = task_result.parameters.get("unit")
        if unit == "tokens":
            unit = "TOKEN"
        elif unit == "stems":
            unit = "STEM"
        else:
            log.error("Unexpected unit '{}', expected 'tokens' or 'stems'".format(task_result.parameters.get("unit")))
            return []
        corpus, corpus_type = self.build_corpus_fields(task_result)

        messages = []
        for word in task_result.task_result["result"]["vocabulary"]:
            interestingness = task_result.task_result["interestingness"].get(word, ProcessorResource.EPSILON)
            for result_idx, result_name in enumerate(["Count", "RelativeCount", "TFIDF"]):
                result = task_result.task_result["result"]["vocabulary"][word][result_idx]
                messages.append(
                    Message(
                        [
                            Fact(
                                corpus,  # corpus
                                corpus_type,  # corpus_type
                                None,  # timestamp_from
                                None,  # timestamp_to
                                "all_time",  # timestamp_type
                                "ExtractWords:" + result_name,  # analysis_type
                                "[{}:{}]".format(unit, word),  # result_key
                                result,  # result_value
                                interestingness,  # outlierness
                            )
                        ]
                    )
                )
        return messages

    def slot_realizer_components(self) -> List[Type[SlotRealizerComponent]]:
        return [EnglishStemRealizer, EnglishTokenRealizer, FinnishStemRealizer, FinnishTokenRealizer]


class EnglishStemRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "en", r"\[STEM:([^\]]+)\]", 1, 'the stem "{}"')


class EnglishTokenRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "en", r"\[TOKEN:([^\]]+)\]", 1, 'the token "{}"')


class FinnishTokenRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "fi", r"\[TOKEN:([^\]]+)\]", 1, 'sane "{}"', attach_attributes_to=[0])


class FinnishStemRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "fi", r"\[STEM:([^\]]+)\]", 1, 'tyvi "{}"', attach_attributes_to=[0])
