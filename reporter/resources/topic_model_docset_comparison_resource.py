import logging
from typing import List, Type

from reporter.core.models import Fact, Message
from reporter.core.realize_slots import RegexRealizer, SlotRealizerComponent, ListRegexRealizer
from reporter.newspaper_message_generator import TaskResult
from reporter.resources.processor_resource import ProcessorResource

log = logging.getLogger("root")


TEMPLATE = """
en: {corpus} share the following topics from {result_key}: {result_value} {analysis_id}
| analysis_type = TopicModelDocsetComparison:Shared:Topics:Multi

en: {corpus} share the topic {result_value} from {result_key} {analysis_id}
| analysis_type = TopicModelDocsetComparison:Shared:Topics:Single

en: {corpus} share no topics from {result_key} {analysis_id}
| analysis_type = TopicModelDocsetComparison:Shared:Topics:None

en: the shared topics of {corpus} have {result_key} of {result_value} {analysis_id}
| analysis_type = TopicModelDocsetComparison:Shared:JSD

en: {corpus} has the following distinct topics from {result_key}: {result_value} {analysis_id}
| analysis_type = TopicModelDocsetComparison:Distinct:Topics:Multi

en: {corpus} has the the distinct topic {result_value} from {result_key} {analysis_id}
| analysis_type = TopicModelDocsetComparison:Distinct:Topics:Single

en: {corpus} has no distinct topics from {result_key} {analysis_id}
| analysis_type = TopicModelDocsetComparison:Distinct:Topics:None

en: {corpus} has {result_key} of {result_value} {analysis_id}
| analysis_type = TopicModelDocsetComparison:Distinct:JSD
"""


class TopicModelDocsetComparisonResource(ProcessorResource):
    def templates_string(self) -> str:
        return TEMPLATE

    def _shared_topics_message_parser(self, task_result: TaskResult) -> List[Message]:
        messages = []

        corpus, corpus_type = self.build_corpus_fields(task_result)
        topics = task_result.task_result.get("result").get("shared_topics")
        result_key = "[TopicModelDocsetComparison:TM:{}]".format(task_result.parameters["model_type"].upper(),)

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
        result_key = "[TopicModelDocsetComparison:TM:{}]".format(task_result.parameters["model_type"].upper(),)

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
            return []

        messages = self._shared_topics_message_parser(task_result)
        messages += self._distinct_topics_message_parser(task_result, 1)
        messages += self._distinct_topics_message_parser(task_result, 2)
        return messages

    def slot_realizer_components(self) -> List[Type[SlotRealizerComponent]]:
        return [
            EnglishTopicModelRealizer,
            EnglishTopicRealizer,
            EnglishTopicListRealizer,
            EnglishMeanJSDRealizer,
            EnglishCrossJSDRealizer,
            EnglishInternalJSDRealizer,
        ]


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


class EnglishTopicRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry, "en", r"\[TopicModelDocsetComparison:Topic:([^\]]+)\]", [1], "{}",
        )


class EnglishMeanJSDRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "en",
            r"\[TopicModelDocsetComparison:JSD:Mean\]",
            [],
            "a JSD between the mean document-topic proportions of the collections",
        )


class EnglishCrossJSDRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry, "en", r"\[TopicModelDocsetComparison:JSD:Cross\]", [], "mean cross-set pairwise JSD",
        )


class EnglishInternalJSDRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "en",
            r"\[TopicModelDocsetComparison:JSD:Internal\]",
            [],
            "mean pairwise JSD within the collection",
        )
