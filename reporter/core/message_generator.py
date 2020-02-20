import logging

from reporter.core.pipeline import NLGPipelineComponent

log = logging.getLogger("root")


class NoMessagesForSelectionException(Exception):
    pass


class MessageGenerator(NLGPipelineComponent):
    pass
