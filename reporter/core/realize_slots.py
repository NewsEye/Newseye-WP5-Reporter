from abc import ABC, abstractmethod
import logging
import re
from numbers import Number
from typing import List, Tuple, Iterable, Union, Callable, Optional

from numpy.random.mtrand import RandomState

from .models import DocumentPlanNode, Slot, TemplateComponent, Literal, Message
from .pipeline import NLGPipelineComponent
from .registry import Registry

log = logging.getLogger('root')


class SlotRealizer(NLGPipelineComponent):

    def __init__(self) -> None:
        self._random = None

    def run(self, registry: Registry, random: RandomState, language: str, document_plan: DocumentPlanNode) -> Tuple[DocumentPlanNode]:
        """
        Run this pipeline component.
        """
        log.info("Realizing slots")
        self._registry = registry
        self._random = random
        while self._recurse(document_plan, language.split('-')[0]): pass  # Repeat until no more changes
        return (document_plan, )

    def _recurse(self, this: DocumentPlanNode, language: str) -> bool:
        if not isinstance(this, Message):
            log.debug("Visiting '{}'".format(this))
            return any(self._recurse(child, language) for child in this.children)
        else:
            log.debug("Visiting {}".format(this))
            any_modified = False
            # Use indexes to iterate through the children since the template slots may be edited, added or replaced
            # during iteration. Ugly, but will do for now.
            idx = 0
            while idx < len(this.children):
                child = this.children[idx]
                log.debug('Visiting child {}'.format(child))
                if not isinstance(child, Slot):
                    idx += 1
                    continue
                modified_components = self._realize_slot(language, child)
                if modified_components != [child]:
                    any_modified = True
                this.children[idx:idx+1] = modified_components
                idx += len(modified_components)
            return any_modified

    def _realize_slot(self, language: str, slot: Slot) -> List[TemplateComponent]:
        for slot_realizer in self._registry.get('slot-realizers'):
            assert isinstance(slot_realizer, SlotRealizerComponent)
            if language in slot_realizer.supported_languages() or 'ANY' in slot_realizer.supported_languages():
                success, components = slot_realizer.realize(slot)
                if success:
                    return components
        log.debug("Unable to realize slot {} in language {} with any realizer".format(slot, language))
        return [slot]


class SlotRealizerComponent(ABC):

    @abstractmethod
    def supported_languages(self) -> List[str]:
        pass

    @abstractmethod
    def realize(self, slot: Slot) -> Tuple[bool, List[TemplateComponent]]:
        pass


class NumberRealizer(SlotRealizerComponent):

    def supported_languages(self) -> List[str]:
        return ['ANY']

    def realize(self, slot: Slot) -> Tuple[bool, List[TemplateComponent]]:
        if not isinstance(slot.value, Number):
            return False, []
        return True, [slot]


class RegexRealizer(SlotRealizerComponent):

    def __init__(self,
                 registry: Registry,
                 languages: Union[str, List[str]],
                 regex: str,
                 extracted_groups: Union[int, Iterable[int]],
                 template: Union[str, Iterable[str]],
                 allowed: Optional[Callable[..., bool]] = None
             ) -> None:
        self.registry = registry
        self.languages = languages if isinstance(languages, list) else [languages]
        self.regex = regex
        self.extracted_groups = extracted_groups if isinstance(extracted_groups, Iterable) else [extracted_groups]
        self.templates = [template] if isinstance(template, str) else template
        self.allowed = allowed

    def supported_languages(self) -> List[str]:
        return self.languages

    def realize(self, slot: Slot) -> Tuple[bool, List[TemplateComponent]]:
        if not isinstance(slot.value, str):
            return False, []
        match = re.fullmatch(self.regex, slot.value)
        if match:
            if self.allowed is not None and not self.allowed(*[match.group(i) for i in self.extracted_groups]):
                return False, []
            template_idx = RandomState(self.registry.get('seed')).randint(0, len(self.templates))
            template = self.templates[template_idx]
            log.info('Template: {}'.format(template))
            string_realization = template.format(*[match.group(i) for i in self.extracted_groups])
            log.info('String realization: {}'.format(string_realization))
            components = []
            for realization_token in string_realization.split():
                new_slot = slot.copy(include_fact=True)
                # An ugly hack that ensures the lambda correctly binds to the value of realization_token at this
                # time. Without this, all the lambdas bind to the final value of the realization_token variable, ie.
                # the final value at the end of the loop.  See https://stackoverflow.com/a/10452819
                new_slot.value = lambda f, realization_token=realization_token: realization_token
                components.append(new_slot)
            log.info('Components: {}'.format([str(c) for c in components]))
            return True, components
        return False, []
