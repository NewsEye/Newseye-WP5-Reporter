import logging
from random import Random
from typing import List

from reporter.core import NoMessagesForSelectionException, NLGPipelineComponent, Message, Registry

log = logging.getLogger('root')


class NewspaperMessageGenerator(NLGPipelineComponent):

    def run(self, registry: Registry, random: Random, language: str) -> List[Message]:
        """
        Run this pipeline component.
        """
        messages = []

        if not messages:
            raise NoMessagesForSelectionException()

        return messages
