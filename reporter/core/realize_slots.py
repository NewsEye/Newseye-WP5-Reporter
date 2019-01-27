import logging
from random import Random
import re
from typing import cast, Union

from .document import DocumentPlanNode, Slot, TemplateComponent
from .pipeline import NLGPipelineComponent
from .registry import Registry

log = logging.getLogger('root')


class SlotRealizer(NLGPipelineComponent):

    def __init__(self) -> None:
        self._random = None

    def run(self, registry: Registry, random: Random, language: str, document_plan: DocumentPlanNode) -> DocumentPlanNode:
        """
        Run this pipeline component.
        """
        log.info("Realizing slots")
        self._random = random
        self._recurse(document_plan)
        return document_plan

    def _recurse(self, this: DocumentPlanNode) -> int:
        if not isinstance(this, TemplateComponent):
            log.debug("Visiting non-leaf '{}'".format(this))
            # Use indexes to iterate through the children since the template slots may be edited, added or replaced
            # during iteration. Ugly, but will do for now.
            idx = 0
            while idx < len(this.children):
                slots_added = self._recurse(this.children[idx])
                if slots_added:
                    idx += slots_added
                idx += 1
        else:
            this = cast(TemplateComponent, this)  # Known to be a TemplateComponent, since we are at a leaf node
            log.debug("Visiting leaf {}".format(this))

            try:
                slot_type = this.slot_type
            except AttributeError:
                log.info("Got an AttributeError when checking slot_type in realize_slots. Probably not a slot.")
                slot_type = 'n/a'

            if slot_type == 'what':
                added_slots = self._realize_value(this)
                return added_slots
            # Note that {time} slots aren't handled until at the NER, because they won't be realized every time.
            elif slot_type[:-2] == 'when':
                added_slots = self._realize_time(this)
                return added_slots
            elif slot_type == 'what_type':
                added_slots = self._realize_unit(this)
                return added_slots
            else:
                return 0

    def _realize_value(self, slot: Slot) -> Union[str, int]:
        return slot.value

