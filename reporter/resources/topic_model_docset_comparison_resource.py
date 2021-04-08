import logging
from typing import List, Type

from reporter.core.models import Fact, Message
from reporter.core.realize_slots import RegexRealizer, SlotRealizerComponent, ListRegexRealizer
from reporter.newspaper_message_generator import TaskResult, WrongResourceException
from reporter.resources.processor_resource import ProcessorResource

log = logging.getLogger("root")


TEMPLATE = """
en: {corpus} share the following topics from {result_key}: {result_value} {analysis_id}
fi: {corpus} jakavat seuraavat aiheet {result_key}: {result_value} {analysis_id}
de: {corpus} haben die folgenden Topics eines {result_key} gemeinsam: {result_value} {analysis_id}
fr: {corpus} partagent les sujets suivants à partir {result_key}: {result_value} {analysis_id}
| analysis_type = TopicModelDocsetComparison:Shared:Topics:Multi

en: {corpus} share the topic {result_value} from {result_key} {analysis_id}
fi: {corpus} jakavant aiheen {result_value} {result_key} {analysis_id}
de: {corpus} haben den Topic {result_value} eines {result_key} gemeinsam {analysis_id}
fr: {corpus} partagent le sujet {result_value} à partir {result_key} {analysis_id}
| analysis_type = TopicModelDocsetComparison:Shared:Topics:Single

en: {corpus} share no topics from {result_key} {analysis_id}
fi: {corpus} eivät jaa aiheita {result_key} {analysis_id}
de: {corpus} haben keine gemeinsamen Topics eines {result_key} {analysis_id}.
fr: {corpus} ne partagent aucun sujet issu {result_key} {analysis_id}
| analysis_type = TopicModelDocsetComparison:Shared:Topics:None

en: the shared topics of {corpus} have {result_key} of {result_value} {analysis_id}
fi: {corpus} {result_key} oli {result_value} {analysis_id}
de: Für {corpus} {result_key} {result_value} {analysis_id}
fr: Les sujets partagés par {corpus} ont une {result_key} {result_value} {analysis_id}
| analysis_type = TopicModelDocsetComparison:Shared:JSD

en: {corpus} discussed the following topics from {result_key}: {result_value} {analysis_id}
fi: {corpus} käsitteli seuraavia aiheita {result_key}: {result_value} {analysis_id}
de: {corpus} diskutierte die folgenden Topics eines {result_key}: {result_value} {analysis_id}
fr: {corpus} traite des sujets suivants à partir {result_key}: {result_value} {analysis_id}
| analysis_type = TopicModelDocsetComparison:Distinct:Topics:Multi

en: {corpus} discussed only the topic {result_value} from {result_key} {analysis_id}
fi: {corpus} käsitteli ainoastaan aihetta {result_value} from {result_key} {analysis_id}
de: {corpus} diskutierte nur den Topic {result_value} eines {result_key} {analysis_id}
fr: {corpus} traite du seul sujet {result_value} issu {result_key} {analysis_id}
| analysis_type = TopicModelDocsetComparison:Distinct:Topics:Single

en: {corpus} discussed no topics from {result_key} {analysis_id}
fi: {corpus} ei käsitellyt ainoatakan aihetta {result_key} {analysis_id}
de: {corpus} diskutierte keine Topics eines {result_key} {analysis_id}
fr: {corpus} ne traite d'aucun sujet issu {result_key} {analysis_id}
| analysis_type = TopicModelDocsetComparison:Distinct:Topics:None

en: {corpus} has {result_key} of {result_value} {analysis_id}
fi: {corpus} {result_key} oli {result_value} {analysis_id}
de: {corpus} hat {result_key} von {result_value} {analysis_id}
fr: {corpus} a {result_key} de {result_value} {analysis_id}
| analysis_type = TopicModelDocsetComparison:Distinct:JSD
"""


class TopicModelDocsetComparisonResource(ProcessorResource):
    def templates_string(self) -> str:
        return TEMPLATE

    def _shared_topics_message_parser(self, task_result: TaskResult) -> List[Message]:
        messages = []

        corpus, corpus_type = self.build_corpus_fields(task_result)
        topics = task_result.task_result.get("result").get("shared_topics")
        topics = [str(t) for t in topics]
        result_key = "[TopicModelDocsetComparison:TM:{}]".format(
            task_result.parameters.get("model_type", "LDA").upper(),
        )

        if len(topics) == 0:
            analysis_type = "TopicModelDocsetComparison:Shared:Topics:None"
            result_value = "None"
        elif len(topics) == 1:
            analysis_type = "TopicModelDocsetComparison:Shared:Topics:Single"
            result_value = "[TopicModelDocsetComparison:Topic:{}]".format(topics[0])
        else:
            analysis_type = "TopicModelDocsetComparison:Shared:Topics:Multi"
            result_value = "[TopicModelDocsetComparison:TopicList:{}]".format("|".join(topics))

        interestingness = task_result.task_result.get("interestingness", {}).get("shared_topics", 0)

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

        for variant, field in [("Mean", "mean_jsd"), ("Cross", "cross_jsd")]:
            messages.append(
                Message(
                    Fact(
                        corpus,
                        corpus_type,
                        None,
                        None,
                        "all_time",
                        "TopicModelDocsetComparison:Shared:JSD",
                        "[TopicModelDocsetComparison:JSD:{}]".format(variant),
                        task_result.task_result.get("result").get(field),
                        task_result.task_result.get("interestingness").get(field),
                        "[LINK:{}]".format(task_result.uuid),  # uuid
                    )
                )
            )

        return messages

    def _distinct_topics_message_parser(self, task_result: TaskResult, collection_id: int) -> List[Message]:
        messages = []

        topics_label = "distinct_topics" + str(collection_id)
        collection = "collection" + str(collection_id)

        corpus, corpus_type = self.build_corpus_fields(task_result.parameters.get(collection))
        topics = task_result.task_result.get("result").get(topics_label)
        topics = [str(t) for t in topics]
        result_key = "[TopicModelDocsetComparison:TM:{}]".format(
            task_result.parameters.get("model_type", "LDA").upper(),
        )

        if len(topics) == 0:
            analysis_type = "TopicModelDocsetComparison:Distinct:Topics:None"
            result_value = "None"
        elif len(topics) == 1:
            analysis_type = "TopicModelDocsetComparison:Distinct:Topics:Single"
            result_value = "[TopicModelDocsetComparison:Topic:{}]".format(topics[0])
        else:
            analysis_type = "TopicModelDocsetComparison:Distinct:Topics:Multi"
            result_value = "[TopicModelDocsetComparison:TopicList:{}]".format("|".join(topics))

        interestingness = task_result.task_result.get("interestingness", {}).get(topics_label, 0)

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

        jsd_label = "internal_jsd" + str(collection_id)
        messages.append(
            Message(
                Fact(
                    corpus,
                    corpus_type,
                    None,
                    None,
                    "all_time",
                    "TopicModelDocsetComparison:Distinct:JSD",
                    "[TopicModelDocsetComparison:JSD:Internal]",
                    task_result.task_result.get("result").get(jsd_label),
                    task_result.task_result.get("interestingness").get(jsd_label),
                    "[LINK:{}]".format(task_result.uuid),  # uuid
                )
            )
        )

        return messages

    def parse_messages(self, task_result: TaskResult, context: List[TaskResult], language: str) -> List[Message]:
        if not task_result.processor == "TopicModelDocsetComparison":
            raise WrongResourceException()

        messages = self._shared_topics_message_parser(task_result)
        messages += self._distinct_topics_message_parser(task_result, 1)
        messages += self._distinct_topics_message_parser(task_result, 2)
        return messages

    def slot_realizer_components(self) -> List[Type[SlotRealizerComponent]]:
        return [
            TopicRealizer,
            #
            EnglishTopicModelRealizer,
            EnglishTopicListRealizer,
            EnglishMeanJSDRealizer,
            EnglishCrossJSDRealizer,
            EnglishInternalJSDRealizer,
            #
            FinnishTopicModelRealizer,
            FinnishTopicListRealizer,
            FinnishMeanJSDRealizer,
            FinnishCrossJSDRealizer,
            FinnishInternalJSDRealizer,
            #
            GermanTopicModelRealizer,
            GermanTopicListRealizer,
            GermanMeanJSDRealizer,
            GermanCrossJSDRealizer,
            GermanInternalJSDRealizer,
            #
            FrenchTopicModelRealizer,
            FrenchTopicListRealizer,
            FrenchMeanJSDRealizer,
            FrenchCrossJSDRealizer,
            FrenchInternalJSDRealizer,
        ]


class TopicRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry, "ANY", r"\[TopicModelDocsetComparison:Topic:([^\]]+)\]", [1], "{}",
        )


class EnglishTopicModelRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry, "en", r"\[TopicModelDocsetComparison:TM:([^\]]+)\]", [1], "a {} topic model",
        )


class EnglishTopicListRealizer(ListRegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "en",
            r"\[TopicModelDocsetComparison:TopicList:([^\]]+)\]",
            1,
            "[TopicModelDocsetComparison:Topic:{}]",
            "and",
        )


class EnglishMeanJSDRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "en",
            r"\[TopicModelDocsetComparison:JSD:Mean\]",
            [],
            "a [Tooltip:JSD] between the mean document-topic proportions of the collections",
        )


class EnglishCrossJSDRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry, "en", r"\[TopicModelDocsetComparison:JSD:Cross\]", [], "mean cross-set pairwise [Tooltip:JSD]",
        )


class EnglishInternalJSDRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "en",
            r"\[TopicModelDocsetComparison:JSD:Internal\]",
            [],
            "mean pairwise [Tooltip:JSD] within the collection",
        )


class FinnishTopicModelRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry, "fi", r"\[TopicModelDocsetComparison:TM:([^\]]+)\]", [1], "{}-aihemallin",
        )


class FinnishTopicListRealizer(ListRegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "fi",
            r"\[TopicModelDocsetComparison:TopicList:([^\]]+)\]",
            1,
            "[TopicModelDocsetComparison:Topic:{}]",
            "ja",
        )


class FinnishMeanJSDRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "fi",
            r"\[TopicModelDocsetComparison:JSD:Mean\]",
            [],
            "JSD-samankaltaisuusarvo kokoelmien välillä",
        )


class FinnishCrossJSDRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "fi",
            r"\[TopicModelDocsetComparison:JSD:Cross\]",
            [],
            "keskimääräinen kokoelmien välinen pareittainen JSD-samankaltaisuus",
        )


class FinnishInternalJSDRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "fi",
            r"\[TopicModelDocsetComparison:JSD:Internal\]",
            [],
            "kokoelman sisäinen keskimääräinen pareittainen JSD-samankaltaisuus",
        )


class GermanTopicModelRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry, "de", r"\[TopicModelDocsetComparison:TM:([^\]]+)\]", [1], "{}-Topic-Modells",
        )


class GermanTopicListRealizer(ListRegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "de",
            r"\[TopicModelDocsetComparison:TopicList:([^\]]+)\]",
            1,
            "[TopicModelDocsetComparison:Topic:{}]",
            "und",
        )


class GermanMeanJSDRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "de",
            r"\[TopicModelDocsetComparison:JSD:Mean\]",
            [],
            "beträgt der JSD Wert zwischen den mittleren Dokument-Topic-Anteilen der Kollektionen",
        )


class GermanCrossJSDRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "de",
            r"\[TopicModelDocsetComparison:JSD:Cross\]",
            [],
            "haben einen mittleren cross-set paarweisen JSD von",
        )


class GermanInternalJSDRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "de",
            r"\[TopicModelDocsetComparison:JSD:Internal\]",
            [],
            "einen internen mittleren paarweisen JSD Wert",
        )


class FrenchTopicModelRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry, "fr", r"\[TopicModelDocsetComparison:TM:([^\]]+)\]", [1], "d'un modèle de sujet {}",
        )


class FrenchTopicListRealizer(ListRegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "fr",
            r"\[TopicModelDocsetComparison:TopicList:([^\]]+)\]",
            1,
            "[TopicModelDocsetComparison:Topic:{}]",
            "et",
        )


class FrenchMeanJSDRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "fr",
            r"\[TopicModelDocsetComparison:JSD:Mean\]",
            [],
            "une valeur JSD entre les proportions moyennes document-sujet des collections est",
        )


class FrenchCrossJSDRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry, "fr", r"\[TopicModelDocsetComparison:JSD:Cross\]", [], "un JSD croisé moyen par paire",
        )


class FrenchInternalJSDRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "fr",
            r"\[TopicModelDocsetComparison:JSD:Internal\]",
            [],
            "une valeur interne moyenne JSD par paire",
        )
