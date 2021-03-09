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
| analysis_type = TopicModel:Query:Corpus

en: {result_key} with a weight of {result_value} {analysis_id}
| analysis_type = TopicModel:Query:Document
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

        messages: List[Message] = []

        for (topic, weight, interestingness) in topics:

            if "model_type" in task_result.parameters and "model_name" in task_result.parameters:
                result_key = "[TopicModel:Known:{}:{}:{}]".format(
                    task_result.parameters["model_type"].upper(), task_result.parameters["model_name"], topic
                )
            elif "language" in task_result.parameters:
                result_key = "[TopicModel:Language:{}:{}]".format(task_result.parameters["language"].lower(), topic)
            else:
                result_key = "[TopicModel:Unknown:{}]".format(topic)

            messages.append(
                Message(
                    Fact(
                        corpus,
                        corpus_type,
                        None,
                        None,
                        "all_time",
                        "TopicModel:Query:Corpus",
                        result_key,
                        weight,
                        interestingness,
                        "[LINK:{}]".format(task_result.uuid),  # uuid
                    )
                )
            )

        # Early stop, in case this is an older style of input
        if "doc_ids" not in task_result.task_result["result"]:
            return messages

        docs = list(
            zip(
                task_result.task_result["result"]["doc_ids"],
                task_result.task_result["result"]["doc_weights"],
                task_result.task_result["interestingness"]["doc_weights"],
            )
        )
        for (document, topic_weights, interestingness_values) in docs:
            for ((topic, topic_weight), interestingness) in zip(enumerate(topic_weights), interestingness_values):

                if "model_type" in task_result.parameters and "model_name" in task_result.parameters:
                    result_key = "[TopicModelAndDocument:Known:{}:{}:{}:{}]".format(
                        document,
                        task_result.parameters["model_type"].upper(),
                        task_result.parameters["model_name"],
                        topic,
                    )
                elif "language" in task_result.parameters:
                    result_key = "[TopicModelAndDocument:Language:{}:{}:{}]".format(
                        document, task_result.parameters["language"].lower(), topic
                    )
                else:
                    result_key = "[TopicModelAndDocument:Unknown:{}:{}]".format(document, topic)

                messages.append(
                    Message(
                        Fact(
                            corpus,
                            corpus_type,
                            None,
                            None,
                            "all_time",
                            "TopicModel:Query:Document",
                            result_key,
                            topic_weight,
                            interestingness,
                            "[LINK:{}]".format(task_result.uuid),  # uuid
                        )
                    )
                )

        return messages

    def slot_realizer_components(self) -> List[Type[SlotRealizerComponent]]:
        return [
            EnglishTopicModelRealizer,
            EnglishLanguageTopicModelRealizer,
            EnglishUnknownTopicModelRealizer,
            EnglishKnownTopicModelDocumentRealizer,
            EnglishLanguageTopicModelDocumentRealizer,
            EnglishUnknownTopicModelDocumentRealizer,
            FinnishTopicModelRealizer,
            GermanTopicModelRealizer,
            FrenchTopicModelRealizer,
        ]


class EnglishTopicModelRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "en",
            r"\[TopicModel:Known:([^\]]+):([^\]]+):([^\]]+)\]",
            [3, 1, 2],
            "the topic #{} of the {} topic model {}",
        )


class EnglishLanguageTopicModelRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "en",
            r"\[TopicModel:Language:([^\]]+):([^\]]+)\]",
            [2, 1],
            "the topic #{} of an unnamed [LANGUAGE:{}] language topic model",
        )


class EnglishUnknownTopicModelRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry, "en", r"\[TopicModel:Unknown:([^\]]+)\]", [1], "the topic #{} of an unknown topic model",
        )


class EnglishKnownTopicModelDocumentRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "en",
            r"\[TopicModelAndDocument:Known:([^\]]+):([^\]]+):([^\]]+):([^\]]+)\]",
            [1, 2, 3, 4],
            "document {} is associated with [TopicModel:Known:{}:{}:{}]",
        )


class EnglishLanguageTopicModelDocumentRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "en",
            r"\[TopicModelAndDocument:Language:([^\]]+):([^\]]+):([^\]]+)\]",
            [1, 2, 3],
            "document {} is associated with [TopicModel:Language:{}:{}]",
        )


class EnglishUnknownTopicModelDocumentRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "en",
            r"\[TopicModelAndDocument:Unknown:([^\]]+):([^\]]+)\]",
            [1, 2],
            "document {} is associated with [TopicModel:Unknown:{}]",
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
