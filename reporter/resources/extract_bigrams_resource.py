import logging
from typing import List, Type

from reporter.core.models import Fact, Message
from reporter.core.realize_slots import RegexRealizer, SlotRealizerComponent
from reporter.newspaper_message_generator import TaskResult
from reporter.resources.processor_resource import ProcessorResource

log = logging.getLogger("root")


TEMPLATE = """
en: {result_key} appeared {result_value} times {analysis_id}
fi: {result_key} esiintyi {result_value} kertaa {analysis_id}
de: {result_key} trat {result_val} Mal auf {analysis_id}
| analysis_type = ExtractBigrams:Count

en: {result_key} had a relative count of {result_value} {analysis_id}
fi: {result_key, case=gen} suhteellinen osuus oli {result_value} {analysis_id}
de: {result_key} hatte eine relative Anzahl von {result_value} {analysis_id}
| analysis_type = ExtractBigrams:RelativeCount

en: {result_key} had a Dice score of {result_value} {analysis_id}
fi: {result_key, case=gen} Dice-luku oli {result_value} {analysis_id}
de: {result_key} hatte eine Dice-Wertung von {result_value} {analysis_id}
| analysis_type = ExtractBigrams:DiceScore
"""


class ExtractBigramsResource(ProcessorResource):
    def templates_string(self) -> str:
        return TEMPLATE

    def parse_messages(self, task_result: TaskResult, context: List[TaskResult]) -> List[Message]:
        if not task_result.processor == "ExtractBigrams":
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
        for bigram, results in task_result.task_result["result"].items():
            interestingness = task_result.task_result["interestingness"].get(bigram, ProcessorResource.EPSILON)
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
                                "[{}PAIR:{}]".format(unit, bigram),  # result_key
                                result,  # result_value
                                interestingness,  # outlierness
                                "[LINK:{}]".format(task_result.uuid),  # uuid
                            )
                        ]
                    )
                )
        return messages

    def slot_realizer_components(self) -> List[Type[SlotRealizerComponent]]:
        return [
            EnglishStemPairRealizer,
            EnglishTokenPairRealizer,
            FinnishStemPairRealizer,
            FinnishTokenPairRealizer,
            GermanStemPairRealizer,
            GermanTokenPairRealizer,
        ]


class EnglishTokenPairRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "en", r"\[TOKENPAIR:([^\]]+)\]", 1, 'the token pair "{}"')


class EnglishStemPairRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "en", r"\[STEMPAIR:([^\]]+)\]", 1, 'the stem pair "{}"')


class FinnishTokenPairRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "fi", r"\[TOKENPAIR:([^\]]+)\]", 1, 'sanepari "{}"', attach_attributes_to=[0])


class FinnishStemPairRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "fi", r"\[STEMPAIR:([^\]]+)\]", 1, 'tyvipari "{}"', attach_attributes_to=[0])


class GermanTokenPairRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "de", r"\[TOKENPAIR:([^\]]+)\]", 1, 'das Token-Paar "{}"')


class GermanStemPairRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "de", r"\[STEMPAIR:([^\]]+)\]", 1, 'das Suchwort-Paar "{}"')
