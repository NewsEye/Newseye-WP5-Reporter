import logging
from typing import List, Type

from reporter.core.models import Fact, Message
from reporter.core.realize_slots import ListRegexRealizer, RegexRealizer, SlotRealizerComponent
from reporter.newspaper_message_generator import TaskResult
from reporter.resources.processor_resource import ProcessorResource

log = logging.getLogger("root")


TEMPLATE = """
en: based on topic modelling, the following similar articles were identified: {result_value}
fi: aihemallinnus tunnisti seuraavat samankaltaiset artikkelit: {result_value}
| analysis_type = TopicModel:DocumentLinking:Multiple

en: based on topic modelling, the article {result_value} was identified as highly similar
fi: aihemallinnus tunnisti artikkeling {result_value} hyvin samankaltaiseksi
| analysis_type = TopicModel:DocumentLinking:Single
"""


class TopicModelDocumentLinkingResource(ProcessorResource):
    def templates_string(self) -> str:
        return TEMPLATE

    def parse_messages(self, task_result: TaskResult, context: List[TaskResult]) -> List[Message]:
        if not task_result.processor == "TopicModelDocumentLinking":
            return []

        corpus, corpus_type = self.build_corpus_fields(task_result)
        articles_with_interestingness = [
            (article, interestingness)
            for (article, interestingness) in zip(
                task_result.task_result["result"]["similar_docs"], task_result.task_result["interestingness"]["linking"]
            )
        ]
        articles_with_interestingness = sorted(articles_with_interestingness, key=lambda pair: pair[1], reverse=True)

        single_or_multiple = "Single" if len(articles_with_interestingness) == 1 else "Multiple"

        return [
            Message(
                Fact(
                    corpus,
                    corpus_type,
                    None,
                    None,
                    "all_time",
                    "TopicModel:DocumentLinking:" + single_or_multiple,
                    "LinkedArticles",
                    "[LinkedArticleList:{}]".format(
                        "|".join([article for (article, interestingness) in articles_with_interestingness])
                    ),
                    task_result.task_result["interestingness"]["overall"],
                )
            )
        ]

    def slot_realizer_components(self) -> List[Type[SlotRealizerComponent]]:
        return [EnglishLinkedArticleListRealizer, LinkedArticleRealizer, FinnishLinkedArticleListRealizer]


class EnglishLinkedArticleListRealizer(ListRegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "en", r"\[LinkedArticleList:([^\]]+)\]", 1, "[LinkedArticle:{}]", "and")


class LinkedArticleRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "ANY", r"\[LinkedArticle:([^\]]+)\]", 1, "{}")


class FinnishLinkedArticleListRealizer(ListRegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "fi", r"\[LinkedArticleList:([^\]]+)\]", 1, "[LinkedArticle:{}]", "ja")
