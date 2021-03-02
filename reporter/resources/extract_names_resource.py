import logging
from typing import List, Type

from reporter.core.models import Fact, Message
from reporter.core.realize_slots import RegexRealizer, SlotRealizerComponent, ListRegexRealizer
from reporter.newspaper_message_generator import TaskResult
from reporter.resources.processor_resource import ProcessorResource

log = logging.getLogger("root")


TEMPLATE = """
en: the most prominent name {analysis_id} in the corpus was {result_value}
fi: korpuksessa esiintyivät tärkeimpänä {analysis_id} nimenä {result_value}
de: Die Wichtigkeit Einheiten Namen im Korpus waren: {result_value}
fr: les noms les plus importants du corpus étaient: {result_value}
| analysis_type = ExtractNames:Multiple

en: the most prominent entities {analysis_id} in the corpus were: {result_value}
fi: korpuksessa esiintyivät tärkeimpinä {analysis_id} seuraavat entiteetit: {result_value}
de: Der Wichtigkeit Name im Korpus war {result_value}
fr: le nom le plus important du corpus était {result_value}
| analysis_type = ExtractNames:Single
"""


class ExtractNamesResource(ProcessorResource):
    def templates_string(self) -> str:
        return TEMPLATE

    def parse_messages(self, task_result: TaskResult, context: List[TaskResult]) -> List[Message]:
        if not task_result.processor == "ExtractNames":
            return []

        corpus, corpus_type = self.build_corpus_fields(task_result)

        for entity in task_result.task_result["result"]:
            task_result.task_result["result"][entity]["entity"] = entity

        entities_with_interestingness = [
            (entity, max(interestingness.values()))
            for (entity, interestingness) in zip(
                task_result.task_result["result"].values(), task_result.task_result["interestingness"].values()
            )
        ]

        entities_with_interestingness = sorted(entities_with_interestingness, key=lambda pair: pair[1], reverse=True)

        max_interestingness = entities_with_interestingness[0][1]

        if max_interestingness < 0.01:
            entities_with_interestingness = entities_with_interestingness[0]

        else:
            entities_with_interestingness = [
                (entity, interestingness)
                for (entity, interestingness) in entities_with_interestingness
                if interestingness >= 0.01
            ]

        single_or_multiple = "Single" if len(entities_with_interestingness) == 1 else "Multiple"

        return [
            Message(
                Fact(
                    corpus,
                    corpus_type,
                    None,
                    None,
                    "all_time",
                    "ExtractNames:" + single_or_multiple,
                    "ExtractNames",
                    "[ExtractNamesList:{}]".format(
                        "|".join(
                            [
                                "{}:{}:{}".format(entity["entity"], entity["salience"], entity["stance"])
                                for (entity, interestingness) in entities_with_interestingness
                            ]
                        )
                    ),
                    task_result.task_result["interestingness"]["overall"],
                    "[LINK:{}]".format(task_result.uuid),  # uuid
                )
            )
        ]

    def slot_realizer_components(self) -> List[Type[SlotRealizerComponent]]:
        return [EnglishExtractedNamesListRealizer, EnglishExtractNamesEntityRealizer]


class EnglishExtractedNamesListRealizer(ListRegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "en", r"\[ExtractNamesList:([^\]]+)\]", 1, "[ExtractNames:Entity:{}]", "and")


class EnglishExtractNamesEntityRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "en",
            r"\[ExtractNames:Entity:([^:\]]+):([^:\]]+):([^:\]]+)\]",
            (1, 2, 3),
            "[Entity:Name:{}] (salience = {} , stance = {}",
        )
