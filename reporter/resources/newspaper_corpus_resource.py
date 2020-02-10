from typing import List

from reporter.core import Message
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

