import logging
from typing import List, Type

from reporter.core.models import Fact, Message
from reporter.core.realize_slots import RegexRealizer, SlotRealizerComponent
from reporter.newspaper_message_generator import TaskResult
from reporter.resources.processor_resource import ProcessorResource

log = logging.getLogger("root")


TEMPLATE = """
en: the corpus is associated with {result_key} with a weight of {result_value} {analysis_id}
fi: kokoelman tekstit liittyvät {result_key} painolla {result_value} {analysis_id}
de: Der Korpus ist mit {result_key} mit einem Gewicht von {result_value} verbunden {analysis_id}
fr: le corpus est associé au {result_key} avec un poids de {result_value} {analysis_id}
| analysis_type = TopicModel:Query
"""


class QueryTopicModelResource(ProcessorResource):
    def templates_string(self) -> str:
        return TEMPLATE

    def parse_messages(self, task_result: TaskResult, context: List[TaskResult], language: str) -> List[Message]:
        if not task_result.processor == "QueryTopicModel":
            return []

        corpus, corpus_type = self.build_corpus_fields(task_result)

        topics = [
            (topic, weight, interestingness)
            for ((topic, weight), interestingness) in zip(
                enumerate(task_result.task_result["result"]["topic_weights"]),
                task_result.task_result["interestingness"]["topic_weights"],
            )
        ]

        return [
            Message(
                Fact(
                    corpus,
                    corpus_type,
                    None,
                    None,
                    "all_time",
                    "TopicModel:Query",
                    "[TopicModel:{}:{}:{}]".format(
                        task_result.parameters["model_type"].upper(), task_result.parameters["model_name"], topic
                    ),
                    weight,
                    interestingness,
                    "[LINK:{}]".format(task_result.uuid),  # uuid
                )
            )
            for (topic, weight, interestingness) in topics
        ]

    def slot_realizer_components(self) -> List[Type[SlotRealizerComponent]]:
        return [
            EnglishTopicModelRealizer,
            FinnishTopicModelRealizer,
            GermanTopicModelRealizer,
            FrenchTopicModelRealizer,
        ]


class EnglishTopicModelRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "en",
            r"\[TopicModel:([^\]]+):([^\]]+):([^\]]+)\]",
            [3, 1, 2],
            "the topic #{} of the {} topic model {}",
        )


class FinnishTopicModelRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry, "fi", r"\[TopicModel:([^\]]+):([^\]]+):([^\]]+)\]", [1, 2, 3], "{}-aihemallin {} aiheeseen #{}"
        )


class GermanTopicModelRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "de",
            r"\[TopicModel:([^\]]+):([^\]]+):([^\]]+)\]",
            [3, 1, 2],
            "Thema #{} des {} Topic Models '{}'",
        )


class FrenchTopicModelRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "fr",
            r"\[TopicModel:([^\]]+):([^\]]+):([^\]]+)\]",
            [3, 1, 2],
            'thème n° {} du modèle thématique {} "{}"',
        )
