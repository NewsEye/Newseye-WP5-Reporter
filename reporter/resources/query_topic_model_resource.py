import logging
from typing import List, Type

from reporter.core.models import Fact, Message
from reporter.core.realize_slots import RegexRealizer, SlotRealizerComponent, ListRegexRealizer
from reporter.newspaper_message_generator import TaskResult, WrongResourceException
from reporter.resources.processor_resource import ProcessorResource

log = logging.getLogger("root")


TEMPLATE = """
en: the corpus is the most associated with the following {result_key} topics: {result_value} {analysis_id}
fi: kokoelman tekstit liittyvät seuraaviin {result_key, case=gen} aiheisiin {result_value} {analysis_id}
de: Der Korpus ist mit den folgenden {result_key} Themen am meisten verbunden: {result_value} {analysis_id}
fr: le jeu de données est le plus associé aux sujet {result_key} suivant: {result_value} {analysis_id}
| analysis_type = TopicModel:Query:Corpus:Multi

en: the corpus is only associated with a single {result_key} topic: {result_value} {analysis_id}
fi: kokoelman tekstit liittyvät ainoastaan yhteen {result_key, case=gen} aiheeseen: {result_value} {analysis_id}
de: Der Korpus ist nur mit einem einzigen {result_key} Thema verbunden ist: {result_value} {analysis_id}
fr: le jeu de données est uniquement associé au sujet {result_key} suivant: {result_value} {analysis_id}
| analysis_type = TopicModel:Query:Corpus:Single

en: the corpus is not associated with any {result_key} topics {analysis_id}
fi: kokoelman tekstit eivät liity yhteenkään {result_key, case=gen} aiheeseen {analysis_id}
de: Der Korpus ist nicht mit {result_key} Themen zugeordnet {analysis_id}
fr: le jeu de données n'est associé à aucun sujet {result_key} {analysis_id}
| analysis_type = TopicModel:Query:Corpus:None

en: the document {result_key} is most associated with {result_value} {analysis_id}
fi: dokumentti {result_key} liittyy eniten {result_value, case=gen} {analysis_id}
de: Das Dokument {result_key} ist am häufigsten mit {result_value} verbunden {analysis_id}
fr: le document {result_key} est le plus associé aux {result_value} suivant {analysis_id}
| analysis_type = TopicModel:Query:Document:Multi

en: the document {result_key} is associated with {result_value} {analysis_id}
fi: dokumentti {result_key} liittyy {result_value, case=gen} {analysis_id}
de: Das Dokument {result_key} ist {result_value} verbunden {analysis_id}
fr: le document {result_key} est associé au {result_value} suivant {analysis_id}
| analysis_type = TopicModel:Query:Document:Single

en: the document {result_key} is not associated with any topics from {result_value} {analysis_id}
fi: dokumentti {result_key} ei liity yhteenkään {result_value, case=gen} aiheeseen {analysis_id}
de: Das Dokument {result_key} ist keinem Thema aus einem {result_value} zugeordnet {analysis_id}
fr: le document {result_key} n'est associé à aucun sujet {result_value} {analysis_id}
| analysis_type = TopicModel:Query:Document:None
"""


class QueryTopicModelResource(ProcessorResource):
    def templates_string(self) -> str:
        return TEMPLATE

    @staticmethod
    def _parse_corpus_topics(task_result: TaskResult, corpus: str, corpus_type: str) -> List[Message]:
        messages: List[Message] = []

        if "model_name" in task_result.parameters:
            result_key = "[TopicModel:Named:{}]".format(task_result.parameters["model_name"])
        elif "language" in task_result.parameters:
            result_key = "[TopicModel:Language:{}]".format(task_result.parameters["language"].lower())
        else:
            result_key = "[TopicModel:Unknown]"

        topics = [
            (topic + 1, weight, interestingness)  # +1 because enumerate is 0-indexed but topics are 1-indexed
            for ((topic, weight), interestingness) in zip(
                enumerate(task_result.task_result["result"]["topic_weights"]),
                task_result.task_result["interestingness"]["topic_weights"],
            )
        ]

        if len(topics) == 0:
            analysis_type = "TopicModel:Query:Corpus:None"
            result_value = None
            interestingness = 0.001
        elif len(topics) == 1:
            analysis_type = "TopicModel:Query:Corpus:Single"
            result_value = "[TopicModel:Query:Corpus:TopicWeight:{}:{}]".format(topics[0][0], topics[0][1])
            interestingness = topics[0][2]
        else:
            topics = sorted(topics, key=lambda t: t[2])[: min(3, len(topics))]
            analysis_type = "TopicModel:Query:Corpus:Multi"
            result_value = "[TopicModel:Query:Corpus:TopicWeightList:{}]".format(
                "|".join([f"{topic}:{weight}" for (topic, weight, _) in topics])
            )
            interestingness = max(interestingness for (_, _, interestingness) in topics)

        messages.append(
            Message(
                Fact(
                    corpus,
                    corpus_type,
                    None,
                    None,
                    "all_time",
                    analysis_type,
                    result_key,
                    result_value,
                    interestingness,
                    "[LINK:{}]".format(task_result.uuid),  # uuid
                )
            )
        )

        return messages

    @staticmethod
    def _parse_document_topics(task_result: TaskResult, corpus: str, corpus_type: str) -> List[Message]:
        messages: List[Message] = []

        docs = list(
            zip(
                task_result.task_result["result"]["doc_ids"],
                task_result.task_result["result"]["doc_weights"],
                task_result.task_result["interestingness"]["doc_weights"],
            )
        )

        for (document, topic_weights, interestingness_values) in docs:

            topics = zip(topic_weights, interestingness_values)
            # topic + 1 because enumerate is 0-indexed but topics are 1-indexed
            topics = [(topic + 1, weight, interestingness) for (topic, (weight, interestingness)) in enumerate(topics)]
            topics = [
                (topic, weight, interestingness) for (topic, weight, interestingness) in topics if interestingness > 0
            ]

            if "model_name" in task_result.parameters:
                topic_model = "Named:{}".format(task_result.parameters["model_name"])
            elif "language" in task_result.parameters:
                topic_model = "Language:{}".format(task_result.parameters["language"].lower())
            else:
                topic_model = "Unknown"

            result_key = "[TopicModel:Query:Article:{}]".format(document)
            if len(topics) == 0:
                analysis_type = "TopicModel:Query:Document:None"
                result_value = "[TopicModel:Query:Document:None:{}".format(topic_model)
                interestingness = 0.001
            elif len(topics) == 1:
                analysis_type = "TopicModel:Query:Document:Single"
                result_value = "[TopicModel:Query:Document:TopicWeight:{}:{}:{}]".format(
                    topic_model, topics[0][0], topics[0][1]
                )
                interestingness = topics[0][2]
            else:
                topics = sorted(topics, key=lambda t: t[2])[: min(3, len(topics))]
                analysis_type = "TopicModel:Query:Document:Multi"
                result_value = "[TopicModel:Query:Document:TopicWeightList:{}]".format(
                    "|".join([f"{topic_model}:{topic}:{weight}" for (topic, weight, _) in topics])
                )
                interestingness = max(interestingness for (_, _, interestingness) in topics)

            messages.append(
                Message(
                    Fact(
                        corpus,
                        corpus_type,
                        None,
                        None,
                        "all_time",
                        analysis_type,
                        result_key,
                        result_value,
                        interestingness,
                        "[LINK:{}]".format(task_result.uuid),  # uuid
                    )
                )
            )

        return messages

    def parse_messages(self, task_result: TaskResult, context: List[TaskResult], language: str) -> List[Message]:
        if not task_result.processor == "QueryTopicModel":
            raise WrongResourceException()

        corpus, corpus_type = self.build_corpus_fields(task_result)

        messages = self._parse_corpus_topics(task_result, corpus, corpus_type)

        # Early stop, in case this is an older style of input
        if "doc_ids" not in task_result.task_result["result"]:
            return messages
        messages.extend(self._parse_document_topics(task_result, corpus, corpus_type))

        return messages

    def slot_realizer_components(self) -> List[Type[SlotRealizerComponent]]:
        return [
            LinkedArticleRealizer,
            #
            EnglishTopicModelRealizer,
            EnglishLanguageTopicModelRealizer,
            EnglishUnknownTopicModelRealizer,
            EnglishCorpusTopicWeightListRealizer,
            EnglishCorpusTopicWeightRealizer,
            EnglishDocumentWeightListRealizer,
            EnglishDocumentWeightRealizer,
            EnglishDocumentTopicWeightNoneRealizer,
            #
            FinnishTopicModelRealizer,
            FinnishLanguageTopicModelRealizer,
            FinnishUnknownTopicModelRealizer,
            FinnishCorpusTopicWeightListRealizer,
            FinnishCorpusTopicWeightRealizer,
            FinnishDocumentWeightListRealizer,
            FinnishDocumentWeightRealizer,
            FinnishDocumentTopicWeightNoneRealizer,
            #
            GermanTopicModelRealizer,
            GermanLanguageTopicModelRealizer,
            GermanUnknownTopicModelRealizer,
            GermanCorpusTopicWeightListRealizer,
            GermanCorpusTopicWeightRealizer,
            GermanDocumentWeightListRealizer,
            GermanDocumentWeightRealizer,
            GermanDocumentTopicWeightNoneRealizer,
            #
            FrenchTopicModelRealizer,
            FrenchLanguageTopicModelRealizer,
            FrenchUnknownTopicModelRealizer,
            FrenchCorpusTopicWeightListRealizer,
            FrenchCorpusTopicWeightRealizer,
            FrenchDocumentWeightListRealizer,
            FrenchDocumentWeightRealizer,
            FrenchDocumentTopicWeightNoneRealizer,
        ]


class LinkedArticleRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "ANY", r"\[TopicModel:Query:Article:([^\]]+)\]", (1, 1), "{} [LINK:ARTICLE:{}]")


class EnglishTopicModelRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry, "en", r"\[TopicModel:Named:([^\]]+)\]", [1], "'{}' topic model",
        )


class EnglishLanguageTopicModelRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry, "en", r"\[TopicModel:Language:([^\]]+)\]", [1], "[ENTITY:LANGUAGE:{}] language topic model",
        )


class EnglishUnknownTopicModelRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry, "en", r"\[TopicModel:Unknown\]", [], "topic model",
        )


class EnglishCorpusTopicWeightRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "en",
            r"\[TopicModel:Query:Corpus:TopicWeight:([^\]]+):([^\]]+)\]",
            [1, 2],
            "{} ( [Tooltip:TMWeight] = {} )",
        )


class EnglishCorpusTopicWeightListRealizer(ListRegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "en",
            r"\[TopicModel:Query:Corpus:TopicWeightList:([^\]]+)\]",
            1,
            "[TopicModel:Query:Corpus:TopicWeight:{}]",
            "and",
        )


class EnglishDocumentWeightRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "en",
            r"\[TopicModel:Query:Document:TopicWeight:([^\]]+):([^:\]]+):([^:\]]+)\]",
            [2, 3],
            "topic {} ( [Tooltip:TMWeight] = {} )",
        )


class EnglishDocumentWeightListRealizer(ListRegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "en",
            r"\[TopicModel:Query:Document:TopicWeightList:([^\]]+)\]",
            1,
            "[TopicModel:Query:Document:TopicWeight:{}]",
            "and",
        )


class EnglishDocumentTopicWeightNoneRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry, "en", r"\[TopicModel:Query:Document:None:([^\]]+)\]", [1], "[TopicModel:{}]",
        )


class FinnishTopicModelRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry, "fi", r"\[TopicModel:Named:([^\]]+)\]", [1], "'{}' aihemallin", attach_attributes_to=None,
        )


class FinnishLanguageTopicModelRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "fi",
            r"\[TopicModel:Language:([^\]]+)\]",
            [1],
            "[ENTITY:LANGUAGE:{}] kielisen aihemallin",
            attach_attributes_to=[0],
        )


class FinnishUnknownTopicModelRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "fi", r"\[TopicModel:Unknown\]", [], "aihemallin", attach_attributes_to=None)


class FinnishCorpusTopicWeightRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "fi",
            r"\[TopicModel:Query:Corpus:TopicWeight:([^\]]+):([^\]]+)\]",
            [1, 2],
            "{} ( paino = {} )",
            attach_attributes_to=[0],
        )


class FinnishCorpusTopicWeightListRealizer(ListRegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "fi",
            r"\[TopicModel:Query:Corpus:TopicWeightList:([^\]]+)\]",
            1,
            "[TopicModel:Query:Corpus:TopicWeight:{}]",
            "ja",
            attach_attributes_to=[0],
        )


class FinnishDocumentWeightRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "fi",
            r"\[TopicModel:Query:Document:TopicWeight:([^\]]+):([^:\]]+):([^:\]]+)\]",
            [2, 3],
            "aiheeseen {} ( paino = {} )",
            attach_attributes_to=[0],
        )


class FinnishDocumentWeightListRealizer(ListRegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "fi",
            r"\[TopicModel:Query:Document:TopicWeightList:([^\]]+)\]",
            1,
            "[TopicModel:Query:Document:TopicWeight:{}]",
            "ja",
            attach_attributes_to=[0],
        )


class FinnishDocumentTopicWeightNoneRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "fi",
            r"\[TopicModel:Query:Document:None:([^\]]+)\]",
            [1],
            "[TopicModel:{}]",
            attach_attributes_to=[0],
        )


class GermanTopicModelRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry, "de", r"\[TopicModel:Named:([^\]]+)\]", [1], "'{}' Topic-Modell",
        )


class GermanLanguageTopicModelRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry, "de", r"\[TopicModel:Language:([^\]]+)\]", [1], "[ENTITY:LANGUAGE:{}] Topic-Modell",
        )


class GermanUnknownTopicModelRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry, "de", r"\[TopicModel:Unknown\]", [], "Topic-Modell",
        )


class GermanCorpusTopicWeightRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry, "de", r"\[TopicModel:Query:Corpus:TopicWeight:([^\]]+):([^\]]+)\]", [1, 2], "{} ( Schwere = {} )",
        )


class GermanCorpusTopicWeightListRealizer(ListRegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "de",
            r"\[TopicModel:Query:Corpus:TopicWeightList:([^\]]+)\]",
            1,
            "[TopicModel:Query:Corpus:TopicWeight:{}]",
            "und",
        )


class GermanDocumentWeightRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "de",
            r"\[TopicModel:Query:Document:TopicWeight:([^\]]+):([^:\]]+):([^:\]]+)\]",
            [2, 3],
            "dem Topic {} ( Schwere = {} )",
        )


class GermanDocumentWeightListRealizer(ListRegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "de",
            r"\[TopicModel:Query:Document:TopicWeightList:([^\]]+)\]",
            1,
            "[TopicModel:Query:Document:TopicWeight:{}]",
            "und",
        )


class GermanDocumentTopicWeightNoneRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry, "de", r"\[TopicModel:Query:Document:None:([^\]]+)\]", [1], "[TopicModel:{}]",
        )


class FrenchTopicModelRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry, "fr", r"\[TopicModel:Named:([^\]]+)\]", [1], "de modelé de sujet '{}'",
        )


class FrenchLanguageTopicModelRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry, "fr", r"\[TopicModel:Language:([^\]]+)\]", [1], "de modelé de sujet [ENTITY:LANGUAGE:{}]",
        )


class FrenchUnknownTopicModelRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry, "fr", r"\[TopicModel:Unknown\]", [], "de modelé de sujet",
        )


class FrenchCorpusTopicWeightRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "fr",
            r"\[TopicModel:Query:Corpus:TopicWeight:([^\]]+):([^\]]+)\]",
            [1, 2],
            "{} ( l'importance = {} )",
        )


class FrenchCorpusTopicWeightListRealizer(ListRegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "fr",
            r"\[TopicModel:Query:Corpus:TopicWeightList:([^\]]+)\]",
            1,
            "[TopicModel:Query:Corpus:TopicWeight:{}]",
            "et",
        )


class FrenchDocumentWeightRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "fr",
            r"\[TopicModel:Query:Document:TopicWeight:([^\]]+):([^:\]]+):([^:\]]+)\]",
            [2, 3],
            "de sujet {} ( l'importance = {} )",
        )


class FrenchDocumentWeightListRealizer(ListRegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "fr",
            r"\[TopicModel:Query:Document:TopicWeightList:([^\]]+)\]",
            1,
            "[TopicModel:Query:Document:TopicWeight:{}]",
            "et",
        )


class FrenchDocumentTopicWeightNoneRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry, "fr", r"\[TopicModel:Query:Document:None:([^\]]+)\]", [1], "[TopicModel:{}]",
        )
