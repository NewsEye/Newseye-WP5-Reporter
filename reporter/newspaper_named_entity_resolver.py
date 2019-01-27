from random import Random
import re

from .core import EntityNameResolver, Registry, Slot


class NewspaperEntityNameResolver(EntityNameResolver):

    def __init__(self) -> None:
        # [ENTITY:<group1>:<group2>] where group1 and group2 can contain anything but square brackets or double colon
        self._matcher = re.compile("\[(PLACE|TIME):([^\]:]*):([^\]]*)\]")

    def is_entity(self, maybe_entity: str) -> bool:
        # Match and convert the result to boolean
        try:
            return self._matcher.fullmatch(maybe_entity) is not None
        except TypeError:
            print("EntityNameResolver got a number: {} instead of a string".format(maybe_entity))

    def resolve_entity_type(self, entity: str) -> str:
        return self._matcher.match(entity).groups(0)

    def resolve_surface_form(self, registry: Registry, random: Random, language: str, slot: Slot) -> str:
        return slot.value()
