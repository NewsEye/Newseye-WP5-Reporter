import logging
import re
from typing import Tuple

from numpy.random import Generator

from reporter.constants import LANGUAGES
from reporter.core.entity_name_resolver import EntityNameResolver
from reporter.core.models import Slot
from reporter.core.registry import Registry

log = logging.getLogger("root")


class NewspaperEntityNameResolver(EntityNameResolver):
    def __init__(self) -> None:
        # [ENTITY:<group1>:<group2>] where group1 and group2 can contain anything but square brackets or double colon
        self._matcher = re.compile(r"\[ENTITY:([^\]:]*):([^\]]*)\]")

    def is_entity(self, maybe_entity: str) -> bool:
        # Match and convert the result to boolean
        try:
            return self._matcher.fullmatch(maybe_entity) is not None
        except TypeError:
            log.error("EntityNameResolver got a number: {} instead of a string".format(maybe_entity))

    def parse_entity(self, entity: str) -> Tuple[str, str]:
        groups: Tuple[str, str] = tuple(self._matcher.match(entity).groups())
        assert len(groups) == 2
        return tuple(groups)

    def resolve_surface_form(
        self, registry: Registry, random: Generator, language: str, slot: Slot, entity: str, entity_type: str
    ) -> None:
        if entity_type in ["NEWSPAPER_NAME", "NEWSPAPER"]:
            value = entity.replace("_", " ").capitalize()
        elif entity_type == "LANGUAGE":
            value = LANGUAGES.get(language, {}).get(entity)
        elif entity_type == "DATE":
            value = entity[:10]
        elif entity_type == "NAME":
            value = entity
        else:
            return
        # Was one of the matching things
        slot.value = lambda f: value
