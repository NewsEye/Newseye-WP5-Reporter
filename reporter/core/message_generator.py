import logging
from abc import ABC

from .pipeline import NLGPipelineComponent

log = logging.getLogger("root")


class NoMessagesForSelectionException(Exception):
    pass


class MessageGenerator(ABC, NLGPipelineComponent):
    pass
