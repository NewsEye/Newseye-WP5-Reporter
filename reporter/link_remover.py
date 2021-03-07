import re
from typing import Tuple

from reporter.core.pipeline import NLGPipelineComponent
from reporter.core.registry import Registry


class LinkRemover(NLGPipelineComponent):
    def run(self, registry: Registry, random, language: str, text: str, max_score: float) -> Tuple[str, float]:
        text = re.sub(r" \[LINK:[^\]]+ \]", " ", text)  # " [link] " -> " "
        text = re.sub(r"\[LINK:[^\]]+ \]", "", text)  # " [link]" -> ""
        text = re.sub(r" \[LINK:[^\]]+\]", "", text)  # "[link] " -> ""
        while "  " in text:
            text = text.replace("  ", " ")
        return text, max_score
