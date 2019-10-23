import logging
from typing import List, Tuple

from numpy.random import Generator

from .core import Message, NLGPipelineComponent, Registry

log = logging.getLogger("root")


class NewspaperImportanceSelector(NLGPipelineComponent):
    def run(
        self, registry: Registry, random: Generator, language: str, messages: List[Message]
    ) -> Tuple[List[Message]]:
        """
        Runs this pipeline component.
        """
        facts = messages
        scored_messages = self.score_importance(facts)
        sorted_scored_messages = sorted(scored_messages, key=lambda x: float(x.score), reverse=True)
        return (sorted_scored_messages,)

    def score_importance(self, messages: List[Message]) -> List[Message]:
        for msg in messages:
            msg.score = self.score_importance_single(msg)
        return messages

    def score_importance_single(self, message: Message) -> float:
        return message.main_fact.outlierness
