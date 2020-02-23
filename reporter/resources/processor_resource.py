from abc import ABC, abstractmethod
from typing import List, Tuple, Type

from reporter.core.models import Message
from reporter.core.realize_slots import SlotRealizerComponent
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

        if task_result.dataset:
            corpus.append("[dataset:{}]".format(task_result.dataset))
            corpus_type.append("dataset")

        if task_result.search_query:
            q = task_result.search_query.get("q")
            if q:
                corpus.append("[q:{}]".format(q))
                corpus_type.append("query")

            mm = task_result.search_query.get("mm")
            if mm:
                corpus.append("[mm:{}]".format(mm))

            fq = task_result.search_query.get("fq")
            if fq:
                corpus.append("[fq:{}]".format(fq))

        return " ".join(corpus), "_".join(corpus_type)
