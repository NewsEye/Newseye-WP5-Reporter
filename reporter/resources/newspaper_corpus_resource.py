from typing import List, Type

from reporter.core.models import Message
from reporter.core.realize_slots import RegexRealizer, SlotRealizerComponent
from reporter.newspaper_message_generator import TaskResult
from reporter.resources.processor_resource import ProcessorResource

TEMPLATE = """
${anyquery}: query, query_minmatches, query_minmatches_filter, filter, query_filter

en-head: Analysis of a corpus defined by {corpus}
fi-head: Analyysi korpuksesta kyselyllä {corpus}
de-head: Analyse mit der Abfrage {corpus}
| corpus_type in {anyquery}

en-head: Analysis of the complete corpus
fi-head: Analyysi koko korpuksesta
de-head: Analyse des gesamten Korpus
| corpus_type = full_corpus
"""


class NewspaperCorpusResource(ProcessorResource):
    def templates_string(self) -> str:
        return TEMPLATE

    def parse_messages(self, task_result: TaskResult, context: List[TaskResult]) -> List[Message]:
        return []

    def slot_realizer_components(self) -> List[Type[SlotRealizerComponent]]:
        slot_realizer_components: List[Type[SlotRealizerComponent]] = [
            EnglishQueryFilterRealizer,
            EnglishQueryRealizer,
            EnglishQueryMmFilterRealizer,
            EnglishQueryMmRealizer,
            FinnishQueryMmFilterRealizer,
            FinnishQueryMmRealizer,
            FinnishQueryFilterRealizer,
            FinnishQueryRealizer,
            GermanQueryMmFilterRealizer,
            GermanQueryMmRealizer,
            GermanQueryFilterRealizer,
            GermanQueryRealizer,
        ]
        slot_realizer_components.append(EnglishQueryMmRealizer)

        return slot_realizer_components


class EnglishQueryRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "en", r"\[q:([^\]:]+)\]", 1, 'the query "{}"')


class EnglishQueryMmRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "en", r"\[q:([^\]:]+)\] \[mm:([^\]:]+)\]", (1, 2), 'the query "{}" (min match = {})')


class EnglishQueryMmFilterRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "en",
            r"\[q:([^\]:]+)\] \[mm:([^\]:]+)\] \[fq:([^\]]+)\]",
            (1, 2, 3),
            'the query "{}" (min match = {}) on data from [{}]',
        )


class EnglishQueryFilterRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "en", r"\[q:([^\]:]+)\] \[fq:([^\]]+)\]", (1, 2), 'the query "{}" on data from [{}]')


class FinnishQueryRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "fi", r"\[q:([^\]:]+)\]", 1, '"{}"')


class FinnishQueryMmRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "fi", r"\[q:([^\]:]+)\] \[mm:([^\]:]+)\]", (1, 2), '"{}" (min match = {})')


class FinnishQueryMmFilterRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "fi",
            r"\[q:([^\]:]+)\] \[mm:([^\]:]+)\] \[fq:([^\]]+)\]",
            (1, 2, 3),
            '"{}" (min match = {}) kohdistuen kokoelmaan [{}]',
        )


class FinnishQueryFilterRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "fi", r"\[q:([^\]:]+)\] \[fq:([^\]]+)\]", (1, 2), '"{}" kohdistuen kokoelmaan [{}]')


class GermanQueryRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "de", r"\[q:([^\]:]+)\]", 1, '"{}"')


class GermanQueryMmRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry, "de", r"\[q:([^\]:]+)\] \[mm:([^\]:]+)\]", (1, 2), 'die Abfrage "{}" (das Minimum Match = {})'
        )


class GermanQueryMmFilterRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "de",
            r"\[q:([^\]:]+)\] \[mm:([^\]:]+)\] \[fq:([^\]]+)\]",
            (1, 2, 3),
            'die Abfrage "{}" (das Minimum Match  = {}) nach Daten von [{}]',
        )


class GermanQueryFilterRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry, "de", r"\[q:([^\]:]+)\] \[fq:([^\]]+)\]", (1, 2), 'die Abfrage "{}" nach Daten von [{}]'
        )
