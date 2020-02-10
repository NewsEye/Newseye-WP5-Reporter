from abc import ABC, abstractmethod
from typing import List

from reporter.core import Message
from reporter.newspaper_message_generator import TaskResult


class ProcessorResource(ABC):

    EPSILON = 0.00000001

    @abstractmethod
    def templates_string(self) -> str:
        pass

    @abstractmethod
    def parse_messages(self, task_result: TaskResult, context: List[TaskResult]) -> List[Message]:
        pass