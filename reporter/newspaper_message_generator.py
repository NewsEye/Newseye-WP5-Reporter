from reporter.core import MessageGenerator, NoMessagesForSelectionException, NLGPipelineComponent

import logging
log = logging.getLogger('root')


class NewspaperMessageGenerator(NLGPipelineComponent):

    def run(self, registry, random, language):
        """
        Run this pipeline component.
        """
        messages = []

        if not messages:
            raise NoMessagesForSelectionException()

        return messages,
