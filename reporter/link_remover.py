import re
from typing import Tuple

from numpy.random.generator import Generator

from reporter.core.pipeline import NLGPipelineComponent
from reporter.core.registry import Registry


class LinkRemover(NLGPipelineComponent):
    def run(self, registry: Registry, random: Generator, language: str, text: str) -> Tuple[str]:
        return (re.sub(r"\[LINK:[^\]]+\]", "", text),)
