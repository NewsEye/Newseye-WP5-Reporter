import logging
from typing import List, Type

from reporter.core import Message, Fact, SlotRealizerComponent, RegexRealizer
from reporter.newspaper_message_generator import TaskResult
from reporter.resources.processor_resource import ProcessorResource


log = logging.getLogger("root")


TEMPLATE = """
en: the bigram {result_key} appeared {result_value} times
fi: sanepari {result_key} esiintyi {result_value} kertaa
| analysis_type = ExtractBigrams:Count

en: the bigram {result_key} had a relative count of {result_value}
fi: saneparin {result_key} suhteellinen osuus kaikista saneista oli {result_value}
| analysis_type = ExtractBigrams:RelativeCount

en: the bigram {result_key} had a Dice score of {result_value}
fi: saneparin {result_key} TF-IDF -luku oli {result_value}
| analysis_type = ExtractBigrams:DiceScore
"""


class ExtractBigramsResource(ProcessorResource):
    def templates_string(self) -> str:
        return TEMPLATE

    def parse_messages(self, task_result: TaskResult, context: List[TaskResult]) -> List[Message]:
        if not task_result.processor == "ExtractBigrams":
            return []

        if task_result.parameters.get("unit") != "stems":
            log.error(
                "Unexpected unit '{}', expected 'stems'".format(task_result.parameters.get("unit"))
            )
            return []

        corpus, corpus_type = self.build_corpus_fields(task_result)

        messages = []
        for word, results in task_result.task_result["result"].items():
            interestingness = task_result.task_result["interestingness"].get(
                word, ProcessorResource.EPSILON
            )
            for result_idx, result_name in enumerate(["Count", "RelativeCount", "DiceScore"]):
                result = results[result_idx]
                messages.append(
                    Message(
                        [
                            Fact(
                                corpus,  # corpus
                                corpus_type,  # corpus_type
                                None,  # timestamp_from
                                None,  # timestamp_to
                                "all_time",  # timestamp_type
                                "ExtractBigrams:" + result_name,  # analysis_type
                                "[BIGRAM:{}]".format(word),  # result_key
                                result,  # result_value
                                interestingness,  # outlierness
                            )
                        ]
                    )
                )
        return messages

    def slot_realizer_components(self) -> List[Type[SlotRealizerComponent]]:
        return [BigramRealizer]


class BigramRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "ANY", r"\[BIGRAM:([^\]]+)\]", 1, '"{}"')
