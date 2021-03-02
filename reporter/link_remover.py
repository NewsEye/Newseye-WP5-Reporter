import re
from typing import Tuple

from reporter.core.pipeline import NLGPipelineComponent
from reporter.core.registry import Registry


class LinkRemover(NLGPipelineComponent):
    def run(self, registry: Registry, random, language: str, text: str, max_score: float) -> Tuple[str, float]:
        return re.sub(r"\[LINK:[^\]]+\]", "", text), max_score
