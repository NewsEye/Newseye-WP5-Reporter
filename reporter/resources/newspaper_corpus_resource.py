from typing import List, Type

from reporter.core.models import Message
from reporter.core.realize_slots import RegexRealizer, SlotRealizerComponent, ListRegexRealizer
from reporter.newspaper_message_generator import TaskResult
from reporter.resources.processor_resource import ProcessorResource

TEMPLATE = """
${simple}: dataset, query, dataset_query

en-head: Analysis of {corpus}
fi-head: Analyysi {corpus}
| corpus_type in {simple}

en-head: Comparison of {corpus}
fi-head: Vertaileva analyysi {corpus}
| corpus_type = multicorpus_comparison
"""


class NewspaperCorpusResource(ProcessorResource):
    def templates_string(self) -> str:
        return TEMPLATE

    def parse_messages(self, task_result: TaskResult, context: List[TaskResult]) -> List[Message]:
        return []

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
            FinnishDatasetPlusRealizer,
            FinnishQueryRealizer,
            FinnishQueryPlusRealizer,
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
        super().__init__(registry, "fi", r"\[dataset:([^\]:]+)\]$", 1, 'kokoelmasta "{}"')


class FinnishDatasetPlusRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "fi", r"\[dataset:([^\]:]+)\] (.*)", (1, 2), 'kokoelmaan "{}" kohdistuneen {}')


class FinnishQueryRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "fi", r"\[query:([^\]:]+)\]$", 1, 'haun "{}" tuloksista')


class FinnishQueryPlusRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "fi", r"\[query:([^\]:]+)\] (.+)$", (1, 2), 'haun "{}" {} tuloksista')
