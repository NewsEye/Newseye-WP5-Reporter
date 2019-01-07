from reporter.core import EntityNameResolver
from reporter.english_realizer import EnglishRealizer

import re


class NewspaperEntityNameResolver(EntityNameResolver):

    def __init__(self):
        # [ENTITY:<group1>:<group2>] where group1 and group2 can contain anything but square brackets or double colon
        self._matcher = re.compile("\[(PLACE|TIME):([^\]:]*):([^\]]*)\]")
        self._realizers = {
            'en': EnglishRealizer(),
        }

    def is_entity(self, maybe_entity):
        # Match and convert the result to boolean
        try:
            return self._matcher.fullmatch(maybe_entity) is not None
        except TypeError:
            print("EntityNameResolver got a number: {} instead of a string".format(maybe_entity))

    def resolve_entity_type(self, code):
        return self._parse_code(code)[0]

    def resolve_surface_form(self, registry, random, language, slot):
        return slot.value()