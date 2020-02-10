from abc import ABC, abstractmethod
from typing import List, Tuple, Type

from reporter.core import Message, SlotRealizerComponent
from reporter.newspaper_message_generator import TaskResult


class ProcessorResource(ABC):

    EPSILON = 0.00000001

    @abstractmethod
    def templates_string(self) -> str:
        pass

    @abstractmethod
    def parse_messages(self, task_result: TaskResult, context: List[TaskResult]) -> List[Message]:
        pass

    @abstractmethod
    def slot_realizer_components(self) -> List[Type[SlotRealizerComponent]]:
        pass

    def build_corpus_fields(self, task_result: "TaskResult") -> Tuple[str, str]:
        corpus = []
        corpus_type = []

        q = task_result.search_query.get("q")
        if q:
            corpus.append("[q:{}]".format(q))
            corpus_type.append("query")

        mm = task_result.search_query.get("mm")
        if mm:
            corpus.append("[mm:{}]".format(mm))
            corpus_type.append("minmatches")

        fq = task_result.search_query.get("fq")
        if fq:
            corpus.append("[fq:{}]".format(fq))
            corpus_type.append("filter")

        return " ".join(corpus), "_".join(corpus_type)
