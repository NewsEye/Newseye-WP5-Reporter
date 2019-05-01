from abc import ABC, abstractmethod
import logging
from random import Random
import re
from typing import List, Tuple, Iterable, Union

from .models import DocumentPlanNode, Slot, TemplateComponent
from .pipeline import NLGPipelineComponent
from .registry import Registry

log = logging.getLogger('root')


class SlotRealizer(NLGPipelineComponent):

    def __init__(self) -> None:
        self._random = None

    def run(self, registry: Registry, random: Random, language: str, document_plan: DocumentPlanNode) -> Tuple[DocumentPlanNode]:
        """
        Run this pipeline component.
        """
        log.info("Realizing slots")
        self._registry = registry
        self._random = random
        self._recurse(document_plan, language)
        return (document_plan, )

    def _recurse(self, this: DocumentPlanNode, language: str) -> int:
        if not isinstance(this, TemplateComponent):
            log.debug("Visiting '{}'".format(this))

            # Use indexes to iterate through the children since the template slots may be edited, added or replaced
            # during iteration. Ugly, but will do for now.
            idx = 0
            while idx < len(this.children):
                slots_added = self._recurse(this.children[idx], language)
                if slots_added:
                    idx += slots_added
                idx += 1
        else:
            log.debug("Visiting {}".format(this))
            if isinstance(this, Slot):
                return self._realize_value(language, this)


    def _realize_value(self, language: str, slot: Slot) -> int:
        for slot_realizer in self._registry.get('slot-realizers'):
            assert isinstance(slot_realizer, SlotRealizerComponent)
            if language in slot_realizer.supported_languages():
                success, slots_added = slot_realizer.realize(slot)
                if success:
                    return slots_added
        else:  # No break
            log.warning("Unable to realize slot {} in language {} with any realizer".format(slot, language))


class SlotRealizerComponent(ABC):

    @abstractmethod
    def supported_languages(self) -> List[str]:
        pass

    @abstractmethod
    def realize(self, slot: Slot) -> Tuple[bool, int]:
        pass


class RegexRealizer(SlotRealizerComponent):

    def __init__(self, language: str, regex: str, extracted_groups: Union[int, Iterable[int]], template: str) -> None:
        self.language = language
        self.regex = regex
        self.extracted_groups = extracted_groups if isinstance(extracted_groups, Iterable) else [extracted_groups]
        self.template = template

    def supported_languages(self) -> List[str]:
        return [self.language]

    def realize(self, slot: Slot) -> Tuple[bool, int]:
        if not isinstance(slot.value, str):
            return False, 0
        match = re.fullmatch(self.regex, slot.value)
        if match:
            slot.value = lambda f: self.template.format(*[match.group(i) for i in self.extracted_groups])
            return True, 0
        return False, 0
