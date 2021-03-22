from typing import List, Type

from reporter.core.models import Message
from reporter.core.realize_slots import RegexRealizer, SlotRealizerComponent, ListRegexRealizer
from reporter.newspaper_message_generator import TaskResult, WrongResourceException
from reporter.resources.processor_resource import ProcessorResource

TEMPLATE = """
${simple}: dataset, query, dataset_query

en-head: Analysis of {corpus}
fi-head: Analyysi jonka kohteena on {corpus}
de-head: Analyse {corpus}
fr-head: L’analyse du {corpus}
| corpus_type in {simple}

en-head: Comparison of {corpus}
fi-head: Vertaileva analyysi jonka kohteina ovat {corpus}
de-head: Vergleich {corpus}
fr-head: Analyse comparative {corpus}
| corpus_type = multicorpus_comparison
"""


class NewspaperCorpusResource(ProcessorResource):
    def templates_string(self) -> str:
        return TEMPLATE

    def parse_messages(self, task_result: TaskResult, context: List[TaskResult], language: str) -> List[Message]:
        # This thing shouldn't *actually* parse anything, ever
        raise WrongResourceException()

    def slot_realizer_components(self) -> List[Type[SlotRealizerComponent]]:
        slot_realizer_components: List[Type[SlotRealizerComponent]] = [
            EnglishDatasetRealizer,
            EnglishQueryRealizer,
            EnglishQueryPlusRealizer,
            EnglishDatasetQueryRealizer,
            EnglishDatasetQueryPlusRealizer,
            EnglishQueryMetaRealizer,
            #
            MultiCorpusRealizer,
            MmRealizer,
            QfRealizer,
            #
            FinnishDatasetRealizer,
            FinnishQueryRealizer,
            FinnishQueryPlusRealizer,
            FinnishDatasetQueryRealizer,
            FinnishDatasetQueryPlusRealizer,
            FinnishQueryMetaRealizer,
            #
            GermanDatasetRealizer,
            GermanQueryRealizer,
            GermanQueryPlusRealizer,
            GermanDatasetQueryRealizer,
            GermanDatasetQueryPlusRealizer,
            GermanQueryMetaRealizer,
            #
            FrenchDatasetRealizer,
            FrenchQueryRealizer,
            FrenchQueryPlusRealizer,
            FrenchDatasetQueryRealizer,
            FrenchDatasetQueryPlusRealizer,
            FrenchQueryMetaRealizer,
        ]

        return slot_realizer_components


class MultiCorpusRealizer(ListRegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "ANY", r"\[multicorpus_comparison:([^\]]+)\]", 1, "[{}]", "and", separator="||")


class EnglishDatasetRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "en", r"\[dataset:([^\]:]+)\]$", 1, 'the dataset "{}"')


class EnglishQueryRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "en", r"\[query:([^\]:]+)\]$", 1, 'the query "{}"')


class EnglishQueryPlusRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "en", r"\[query:([^\]:]+):([^\]]+)\]$", (1, 2), 'the query "{}" ( [query_meta:{}] )')


class EnglishDatasetQueryRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "en",
            r"\[dataset_query:([^\]:]+):([^\]:]+)\]",
            (1, 2),
            'the dataset "{}" filtered by the query "{}"',
        )


class EnglishDatasetQueryPlusRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "en",
            r"\[dataset_query:([^\]:]+):([^\]:]+):([^\]]+)\]",
            (1, 2, 3),
            'the dataset "{}" filtered by the query "{}" ( [query_meta:{}] )',
        )


class EnglishQueryMetaRealizer(ListRegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "en", r"\[query_meta:([^\]]+)\]", 1, "[{}]", "and")


class MmRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "ANY", r"\[mm:([^\]:]+)\]", 1, "min match = {}")


class QfRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "ANY", r"\[qf:([^\]:]+)\]", 1, "qf = {}")


class FinnishDatasetRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "fi", r"\[dataset:([^\]:]+)\]$", 1, 'kokoelma "{}"')


class FinnishQueryRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "fi", r"\[query:([^\]:]+)\]$", 1, 'haku "{}"')


class FinnishQueryPlusRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "en", r"\[query:([^\]:]+):([^\]]+)\]$", (1, 2), 'haku "{}" ( [query_meta:{}] )')


class FinnishDatasetQueryRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry, "fi", r"\[dataset_query:([^\]:]+):([^\]:]+)\]", (2, 1), 'haulla "{}" rajattu kokoelma "{}"',
        )


class FinnishDatasetQueryPlusRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "fi",
            r"\[dataset_query:([^\]:]+):([^\]:]+):([^\]]+)\]",
            (2, 3, 1,),
            'haulla "{}" ( [query_meta:{}] ) rajattu kokoelma "{}"',
        )


class FinnishQueryMetaRealizer(ListRegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "fi", r"\[query_meta:([^\]]+)\]", 1, "[{}]", "ja")


class GermanDatasetRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "de", r"\[dataset:([^\]:]+)\]$", 1, 'des Datensatzes "{}"')


class GermanQueryRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "de", r"\[query:([^\]:]+)\]$", 1, 'die Abfrage "{}"')


class GermanQueryPlusRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry, "de", r"\[query:([^\]:]+):([^\]]+)\]$", (1, 2), 'die Abfrage "{}" ( [query_meta:{}] )'
        )


class GermanDatasetQueryRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "de",
            r"\[dataset_query:([^\]:]+):([^\]:]+)\]",
            (1, 2),
            'des Datensatzes "{}" unter der Bedingung "{}"',
        )


class GermanDatasetQueryPlusRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "de",
            r"\[dataset_query:([^\]:]+):([^\]:]+):([^\]]+)\]",
            (1, 2, 3),
            'des Datensatzes "{}" funter der Bedingung "{}" ( [query_meta:{}] )',
        )


class GermanQueryMetaRealizer(ListRegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "de", r"\[query_meta:([^\]]+)\]", 1, "[{}]", "und")


class FrenchDatasetRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "fr", r"\[dataset:([^\]:]+)\]$", 1, "jeu de données « {} »")


class FrenchQueryRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "fr", r"\[query:([^\]:]+)\]$", 1, "jeu de données défini par la requête « {} »")


class FrenchQueryPlusRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "fr",
            r"\[query:([^\]:]+):([^\]]+)\]$",
            (1, 2),
            "jeu de données défini par la requête « {} » ( [query_meta:{}] )",
        )


class FrenchDatasetQueryRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "fr",
            r"\[dataset_query:([^\]:]+):([^\]:]+)\]",
            (1, 2),
            "jeu de données « {} » filtrée par la requête « {} »",
        )


class FrenchDatasetQueryPlusRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "fr",
            r"\[dataset_query:([^\]:]+):([^\]:]+):([^\]]+)\]",
            (1, 2, 3),
            "jeu de données « {} » filtrée par la requête « {} » ( [query_meta:{}] )",
        )


class FrenchQueryMetaRealizer(ListRegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "fr", r"\[query_meta:([^\]]+)\]", 1, "[{}]", "et")
