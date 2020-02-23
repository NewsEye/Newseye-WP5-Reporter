from typing import List, Type

from reporter.core.models import Message
from reporter.core.realize_slots import RegexRealizer, SlotRealizerComponent
from reporter.newspaper_message_generator import TaskResult
from reporter.resources.processor_resource import ProcessorResource

TEMPLATE = """
${any}: dataset, query, dataset_query

en-head: Analysis of {corpus}
fi-head: Analyysi {corpus}
| corpus_type in {any}
"""


class NewspaperCorpusResource(ProcessorResource):
    def templates_string(self) -> str:
        return TEMPLATE

    def parse_messages(self, task_result: TaskResult, context: List[TaskResult]) -> List[Message]:
        return []

    def slot_realizer_components(self) -> List[Type[SlotRealizerComponent]]:
        slot_realizer_components: List[Type[SlotRealizerComponent]] = [
            EnglishDatasetPlusRealizer,
            EnglishDatasetRealizer,
            EnglishQueryPlusRealizer,
            EnglishQueryRealizer,
            FinnishDatasetRealizer,
            FinnishDatasetPlusRealizer,
            FinnishQueryRealizer,
            FinnishQueryPlusRealizer,
            MmRealizer,
        ]

        return slot_realizer_components


class EnglishDatasetRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "en", r"\[dataset:([^\]:]+)\]$", 1, 'the dataset "{}"')


class EnglishDatasetPlusRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "en", r"\[dataset:([^\]:]+)\] (.*)", (1, 2), 'the dataset "{}" filtered by {}')


class EnglishQueryRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "en", r"\[q:([^\]:]+)\]$", 1, 'the query "{}"')


class EnglishQueryPlusRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "en", r"\[q:([^\]:]+)\] (.+)$", (1, 2), 'the query "{}" {}')


class FinnishDatasetRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "fi", r"\[dataset:([^\]:]+)\]$", 1, 'kokoelmasta "{}"')


class FinnishDatasetPlusRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "fi", r"\[dataset:([^\]:]+)\] (.*)", (1, 2), 'kokoelmaan "{}" kohdistuneen {}')


class FinnishQueryRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "fi", r"\[q:([^\]:]+)\]$", 1, 'haun "{}" tuloksista')


class FinnishQueryPlusRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "fi", r"\[q:([^\]:]+)\] (.+)$", (1, 2), 'haun "{}" {} tuloksista')


class MmRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "ANY", r"\[mm:([^\]:]+)\]", 1, "(min match = {})")
