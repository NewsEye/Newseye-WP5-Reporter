import logging
from typing import List, Type

from reporter.core import Message, Fact, SlotRealizerComponent, RegexRealizer
from reporter.newspaper_message_generator import TaskResult
from reporter.resources.processor_resource import ProcessorResource

log = logging.getLogger("root")


TEMPLATE = """
en: the token {result_key} appeared {result_value} times
fi: sane {result_key} esiintyi {result_value} kertaa
| analysis_type = ExtractWords:Count

en: the token {result_key} had a relative count of {result_value}
fi: saneen {result_key} suhteellinen osuus kaikista saneista oli {result_value}
| analysis_type = ExtractWords:RelativeCount

en: the token {result_key} had a TF-IDF score of {result_value}
fi: saneen {result_key} TF-IDF -luku oli {result_value}
| analysis_type = ExtractWords:TFIDF
"""


class ExtractWordsResource(ProcessorResource):
    def templates_string(self) -> str:
        return TEMPLATE

    def parse_messages(self, task_result: TaskResult, context: List[TaskResult]) -> List[Message]:
        if not task_result.processor == "ExtractWords":
            return []

        if task_result.parameters.get("unit") != "tokens":
            log.error(
                "Unexpected unit '{}', expected 'tokens'".format(task_result.parameters.get("unit"))
            )
            return []

        corpus, corpus_type = self.build_corpus_fields(task_result)

        messages = []
        for word in task_result.task_result["result"]["vocabulary"]:
            interestingness = task_result.task_result["interestingness"].get(
                word, ProcessorResource.EPSILON
            )
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
                                "[TOKEN:{}]".format(word),  # result_key
                                result,  # result_value
                                interestingness,  # outlierness
                            )
                        ]
                    )
                )
        return messages

    def slot_realizer_components(self) -> List[Type[SlotRealizerComponent]]:
        return [TokenRealizer]


class TokenRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "en", r"\[TOKEN:([^\]]+)\]", 1, '"{}"')
