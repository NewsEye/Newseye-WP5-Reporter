import logging
from random import Random
import re

from .models import DocumentPlanNode
from .pipeline import NLGPipelineComponent
from .registry import Registry

log = logging.getLogger('root')


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

    def run(self, registry: Registry, random: Random, language: str, document_plan: DocumentPlanNode) -> str:
        """
        Run this pipeline component.
        """
        log.info("Realizing to text")
        sequences = [c for c in document_plan.children]
        paragraphs = [self.realize(s, language) for s in sequences]
        output = ""
        for p in paragraphs:
            output += self.paragraph_start + p + self.paragraph_end
        return output

    def realize(self, sequence: DocumentPlanNode, language: str) -> str:
        """Realizes a single paragraph."""
        output = ""
        for message in sequence.children:
            template = message.template
            component_values = [str(component.value) for component in template.components]

            sent = " ".join([component_value for component_value in component_values if component_value != ""]).rstrip()
            # Temp fix: remove extra spaces occurring with braces and sometimes before commas.
            sent = re.sub(r'\(\s', r'(', sent)
            sent = re.sub(r'\s\)', r')', sent)
            sent = re.sub(r'\s,', r',', sent)

            if not sent:
                if self.fail_on_empty:
                    raise Exception("Empty sentence in surface realization")
                else:
                    continue
            sent = sent[0].upper() + sent[1:]
            output += self.sentence_start + sent + self.sentence_end
        return output


class HeadlineHTMLSurfaceRealizer(SurfaceRealizer):
    paragraph_start = ""
    paragraph_end = ""
    sentence_end = ""
    sentence_start = ""
    fail_on_empty = True


class BodyHTMLSurfaceRealizer(SurfaceRealizer):
    paragraph_start = "<p>"
    paragraph_end = "</p>"
    sentence_end = ". "
    sentence_start = ""
    fail_on_empty = False
