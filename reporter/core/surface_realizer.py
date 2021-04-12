import logging
import re
from typing import Tuple

from numpy import random

from reporter.core.models import DocumentPlanNode, Message
from reporter.core.pipeline import NLGPipelineComponent
from reporter.core.registry import Registry

log = logging.getLogger("root")


class SurfaceRealizer(NLGPipelineComponent):
    """
    Realizes a DocumentPlan as surface text.

    Assumes that the DocumentPlan corresponds to a structure wherein the root has
    some number of paragraphs as children and each paragraph in turn has some number
    of sentences as children.
    """

    @property
    def paragraph_start(self):
        raise NotImplementedError

    @property
    def paragraph_end(self):
        raise NotImplementedError

    @property
    def sentence_start(self):
        raise NotImplementedError

    @property
    def sentence_end(self):
        raise NotImplementedError

    @property
    def fail_on_empty(self):
        raise NotImplementedError

    def run(
        self, registry: Registry, random: random.Generator, language: str, document_plan: DocumentPlanNode
    ) -> Tuple[str, float]:
        """
        Run this pipeline component.
        """
        log.info("Realizing to text")
        sequences = [c for c in document_plan.children]
        paragraphs, scores = zip(*[self.realize(s) for s in sequences])
        output = ""
        for p in paragraphs:
            output += self.paragraph_start + p + self.paragraph_end
        return output, max(scores)

    def realize(self, sequence: DocumentPlanNode) -> Tuple[str, float]:
        """Realizes a single paragraph."""
        output = ""
        for message in sequence.children:
            if not isinstance(message, Message):
                continue
            template = message.template
            component_values = [str(component.value) for component in template.components]

            sent = " ".join([component_value for component_value in component_values if component_value != ""]).rstrip()
            # Temp fix: remove extra spaces occurring with braces and sometimes before commas.
            while "  " in sent:
                sent = sent.replace("  ", " ")
            sent = re.sub(r"\(\s", r"(", sent)
            sent = re.sub(r"\s\)", r")", sent)
            sent = re.sub(r"\s,", r",", sent)
            sent = re.sub(r"\s\.", r".", sent)
            sent = re.sub(r"\s:", r":", sent)

            if not sent:
                if self.fail_on_empty:
                    raise Exception("Empty sentence in surface realization")
                else:
                    continue
            sent = sent[0].upper() + sent[1:]
            output += self.sentence_start + sent + self.sentence_end
        max_score = max(message.score for message in sequence.children if isinstance(message, Message))
        return output, max_score


class HeadlineHTMLSurfaceRealizer(SurfaceRealizer):
    paragraph_start = "<h4>"
    paragraph_end = "</h4>"
    sentence_end = ""
    sentence_start = ""
    fail_on_empty = True


class BodyHTMLSurfaceRealizer(SurfaceRealizer):
    paragraph_start = "<p>"
    paragraph_end = "</p>"
    sentence_end = ". "
    sentence_start = ""
    fail_on_empty = False


class BodyHTMLListSurfaceRealizer(SurfaceRealizer):
    paragraph_start = "<ul>"
    paragraph_end = "</ul>"
    sentence_end = ".</li>"
    sentence_start = "<li>"
    fail_on_empty = False


class BodyHTMLOrderedListSurfaceRealizer(SurfaceRealizer):
    paragraph_start = "<ol>"
    paragraph_end = "</ol>"
    sentence_end = ".</li>"
    sentence_start = "<li>"
    fail_on_empty = False
