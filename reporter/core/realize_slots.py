import logging
import re
from abc import ABC, abstractmethod
from numbers import Number
from typing import Callable, Iterable, List, Optional, Tuple, Union

from numpy.random import Generator

from reporter.core.models import DocumentPlanNode, Literal, Message, Slot, TemplateComponent
from reporter.core.pipeline import NLGPipelineComponent
from reporter.core.registry import Registry

log = logging.getLogger("root")


class SlotRealizer(NLGPipelineComponent):
    def __init__(self) -> None:
        self._random = None
        self._registry = None

    def run(
        self, registry: Registry, random: Generator, language: str, document_plan: DocumentPlanNode
    ) -> Tuple[DocumentPlanNode]:
        """
        Run this pipeline component.
        """
        log.info("Realizing slots")
        self._registry = registry
        self._random = random
        while self._recurse(document_plan, language.split("-")[0]):
            pass  # Repeat until no more changes
        return (document_plan,)

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
                log.debug("Visiting child {}".format(child))
                if not isinstance(child, Slot):
                    idx += 1
                    continue
                modified_components = self._realize_slot(language, child)
                if modified_components != [child]:
                    any_modified = True
                this.children[idx : idx + 1] = modified_components
                idx += len(modified_components)
            return any_modified

    def _realize_slot(self, language: str, slot: Slot) -> List[TemplateComponent]:
        slot_realizers = self._registry.get("slot-realizers")
        slot_realizers.append(NumberRealizer())
        for slot_realizer in slot_realizers:
            assert isinstance(slot_realizer, SlotRealizerComponent)
            if language in slot_realizer.supported_languages() or "ANY" in slot_realizer.supported_languages():
                success, components = slot_realizer.realize(slot, self._random)
                if success:
                    return components
        log.debug("Unable to realize slot {} in language {} with any realizer".format(slot, language))
        return [slot]


class SlotRealizerComponent(ABC):
    @abstractmethod
    def supported_languages(self) -> List[str]:
        pass

    @abstractmethod
    def realize(self, slot: Slot, random: Generator) -> Tuple[bool, List[TemplateComponent]]:
        pass


class NumberRealizer(SlotRealizerComponent):
    def supported_languages(self) -> List[str]:
        return ["ANY"]

    def realize(self, slot: Slot, random: Generator) -> Tuple[bool, List[TemplateComponent]]:
        value = slot.value
        if not isinstance(value, Number):
            return False, []

        if isinstance(value, (int, float)):
            if int(value) == value:
                slot.value = lambda x: int(value)
                return True, [slot]

            for rounding in range(5):
                if round(value, rounding) != 0:
                    slot.value = lambda x: round(value, rounding + 2)
                    return True, [slot]

        return True, [slot]


class RegexRealizer(SlotRealizerComponent):
    def __init__(
        self,
        registry: Registry,
        languages: Union[str, List[str]],
        regex: str,
        extracted_groups: Union[int, Iterable[int]],
        template: Union[str, Iterable[str]],
        group_requirements: Optional[Callable[..., bool]] = None,
        slot_requirements: Optional[Callable[[Slot], bool]] = None,
        attach_attributes_to: Optional[Iterable[int]] = None,
    ) -> None:
        self.registry = registry
        self.languages = languages if isinstance(languages, list) else [languages]
        self.regex = regex
        self.extracted_groups = extracted_groups if isinstance(extracted_groups, Iterable) else [extracted_groups]
        self.templates = [template] if isinstance(template, str) else template
        self.group_requirements = group_requirements
        self.slot_requirements = slot_requirements
        self.attach_attributes_to = attach_attributes_to if attach_attributes_to is not None else []

    def supported_languages(self) -> List[str]:
        return self.languages

    def realize(self, slot: Slot, random: Generator) -> Tuple[bool, List[TemplateComponent]]:
        # We can only parse the slot contents with a regex if the slot contents are a string
        if not isinstance(slot.value, str):
            return False, []

        match = re.fullmatch(self.regex, slot.value)

        if not match:
            return False, []

        groups = [match.group(i) for i in self.extracted_groups]

        # Check that the requirements placed on the groups are fulfilled
        if self.group_requirements is not None and not self.group_requirements(*groups):
            return False, []

        # Check that the requirements placed on the slot are fulfilled
        if self.slot_requirements is not None and not self.slot_requirements(slot):
            return False, []

        template = random.choice(self.templates)
        log.info("Template: {}".format(template))

        string_realization = template.format(*groups)
        log.info("String realization: {}".format(string_realization))

        components = []
        for idx, realization_token in enumerate(string_realization.split()):
            new_slot = slot.copy(include_fact=True)

            # By default, copy copies the attributes too. In case attach_attributes_to was set,
            # we need to explicitly reset the attributes for all those slots NOT explicitly mentioned
            if idx not in self.attach_attributes_to:
                new_slot.attributes = {}

            # An ugly hack that ensures the lambda correctly binds to the value of realization_token at this
            # time. Without this, all the lambdas bind to the final value of the realization_token variable, ie.
            # the final value at the end of the loop.  See https://stackoverflow.com/a/10452819
            new_slot.value = lambda f, realization_token=realization_token: realization_token
            components.append(new_slot)
        log.info("Components: {}".format([str(c) for c in components]))

        return True, components


class ListRegexRealizer(RegexRealizer):
    def __init__(
        self,
        registry: Registry,
        languages: Union[str, List[str]],
        regex: str,
        extracted_groups: Union[int, Iterable[int]],
        template: Union[str, Iterable[str]],
        combiner: str,
        group_requirements: Optional[Callable[..., bool]] = None,
        slot_requirements: Optional[Callable[[Slot], bool]] = None,
        attach_attributes_to: Optional[Iterable[int]] = None,
    ) -> None:

        super().__init__(
            registry,
            languages,
            regex,
            extracted_groups,
            template,
            group_requirements,
            slot_requirements,
            attach_attributes_to,
        )
        self.combiner = combiner

    def realize(self, slot: Slot, random: Generator) -> Tuple[bool, List[TemplateComponent]]:
        # We can only parse the slot contents with a regex if the slot contents are a string
        if not isinstance(slot.value, str):
            return False, []

        match = re.fullmatch(self.regex, slot.value)

        if not match:
            return False, []

        groups = [match.group(i) for i in self.extracted_groups]

        # Check that the requirements placed on the groups are fulfilled
        if self.group_requirements is not None and not self.group_requirements(*groups):
            return False, []

        # Check that the requirements placed on the slot are fulfilled
        if self.slot_requirements is not None and not self.slot_requirements(slot):
            return False, []

        components = []
        entities = groups[0].split("|")
        for idx, element in enumerate(entities):
            remaining = len(entities) - idx - 1

            template = random.choice(self.templates)
            log.info("Template: {}".format(template))

            string_realization = template.format(element)
            log.info("String realization: {}".format(string_realization))

            for idx, realization_token in enumerate(string_realization.split()):
                new_slot = slot.copy(include_fact=True)

                # By default, copy copies the attributes too. In case attach_attributes_to was set,
                # we need to explicitly reset the attributes for all those slots NOT explicitly mentioned
                if idx not in self.attach_attributes_to:
                    new_slot.attributes = {}

                # An ugly hack that ensures the lambda correctly binds to the value of realization_token at this
                # time. Without this, all the lambdas bind to the final value of the realization_token variable, ie.
                # the final value at the end of the loop.  See https://stackoverflow.com/a/10452819
                new_slot.value = lambda f, realization_token=realization_token: realization_token
                components.append(new_slot)

                if remaining > 1:
                    components.append(Literal(","))
                elif remaining == 1:
                    components.append(Literal(self.combiner))

            log.info("Components: {}".format([str(c) for c in components]))

        return True, components
