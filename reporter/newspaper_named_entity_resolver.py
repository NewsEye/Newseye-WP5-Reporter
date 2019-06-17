from reporter.constants import LANGUAGES
from random import Random
import re
from typing import Tuple

from .core import EntityNameResolver, Registry, Slot

class NewspaperEntityNameResolver(EntityNameResolver):

    def __init__(self) -> None:
        # [ENTITY:<group1>:<group2>] where group1 and group2 can contain anything but square brackets or double colon
        self._matcher = re.compile("\[ENTITY:([^\]:]*):([^\]]*)\]")

    def is_entity(self, maybe_entity: str) -> bool:
        # Match and convert the result to boolean
        try:
            return self._matcher.fullmatch(maybe_entity) is not None
        except TypeError:
            print("EntityNameResolver got a number: {} instead of a string".format(maybe_entity))

    def parse_entity(self, entity: str) -> Tuple[str, str]:
        groups: Tuple[str, str] = tuple(self._matcher.match(entity).groups())
        assert len(groups) == 2
        return tuple(groups)

    def resolve_surface_form(self, registry: Registry, random: Random, language: str, slot: Slot, entity:str, entity_type: str) -> None:
        if entity_type in ['NEWSPAPER_NAME', 'NEWSPAPER']:
                value = entity.replace('_', ' ').capitalize()
        elif entity_type == 'LANGUAGE':
            value = LANGUAGES.get(language, {}).get(entity)
        elif entity_type == 'DATE':
            value = entity[:10]
        else:
            return
        # Was one of the matching things
        slot.value = lambda f: value

