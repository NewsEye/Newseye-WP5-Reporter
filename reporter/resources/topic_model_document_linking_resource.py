import logging
from typing import List, Type

from reporter.core.models import Fact, Message
from reporter.core.realize_slots import ListRegexRealizer, RegexRealizer, SlotRealizerComponent
from reporter.newspaper_message_generator import TaskResult, WrongResourceException
from reporter.resources.processor_resource import ProcessorResource

log = logging.getLogger("root")


TEMPLATE = """
en: based on topic modelling, the following similar articles were identified: {result_value} {analysis_id}
fi: aihemallinnus tunnisti seuraavat samankaltaiset artikkelit: {result_value} {analysis_id}
de: Basierend auf Topic Modelling wurden die folgenden sehr ähnlichen Artikel identifiziert: {result_value} {analysis_id}
fr: Basé sur la modélisation, les articles similaires suivants ont été identifiés: {result_value} {analysis_id}
| analysis_type = TopicModel:DocumentLinking:Multiple

en: based on topic modelling, the article {result_value} was identified as highly similar {analysis_id}
fi: aihemallinnus tunnisti artikkeling {result_value} hyvin samankaltaiseksi {analysis_id}
de: Basierend auf Topic Modelling wurde der Artikel {result_value} als sehr ähnlich zum Korpus identifiziert {analysis_id}
fr: Basé sur la modélisation, l’article {result_value} a été identifié comme étant très similaire au corpus {analysis_id}
| analysis_type = TopicModel:DocumentLinking:Single
"""  # noqa: E501


class TopicModelDocumentLinkingResource(ProcessorResource):
    def templates_string(self) -> str:
        return TEMPLATE

    def parse_messages(self, task_result: TaskResult, context: List[TaskResult], language: str) -> List[Message]:
        if not task_result.processor == "TopicModelDocumentLinking":
            raise WrongResourceException()

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
                    "[LINK:{}]".format(task_result.uuid),  # uuid
                )
            )
        ]

    def slot_realizer_components(self) -> List[Type[SlotRealizerComponent]]:
        return [
            LinkedArticleRealizer,
            #
            EnglishLinkedArticleListRealizer,
            #
            FinnishLinkedArticleListRealizer,
            #
            GermanLinkedArticleListRealizer,
            #
            FrenchLinkedArticleListRealizer,
        ]


class EnglishLinkedArticleListRealizer(ListRegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "en", r"\[LinkedArticleList:([^\]]+)\]", 1, "[LinkedArticle:{}]", "and")


class LinkedArticleRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "ANY", r"\[LinkedArticle:([^\]]+)\]", (1, 1), "{} [LINK:ARTICLE:{}]")


class FinnishLinkedArticleListRealizer(ListRegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "fi", r"\[LinkedArticleList:([^\]]+)\]", 1, "[LinkedArticle:{}]", "ja")


class GermanLinkedArticleListRealizer(ListRegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "de", r"\[LinkedArticleList:([^\]]+)\]", 1, "[LinkedArticle:{}]", "und")


class FrenchLinkedArticleListRealizer(ListRegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "fr", r"\[LinkedArticleList:([^\]]+)\]", 1, "[LinkedArticle:{}]", "et")
