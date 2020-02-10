from abc import ABC, abstractmethod


class ProcessorResource(ABC):
    @abstractmethod
    def templates_string(self) -> str:
        pass
