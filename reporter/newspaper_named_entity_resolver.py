import logging
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple

from numpy.random import Generator

from reporter.core.entity_name_resolver import EntityNameResolver
from reporter.core.models import Slot
from reporter.core.registry import Registry

log = logging.getLogger("root")


class NewspaperEntityNameResolver(EntityNameResolver):
    def __init__(self):
        self._matcher = re.compile(r"\[ENTITY:([^:]+):([^\]]+)\]")
        self.realizers: Dict[str, Dict[str, Dict[str, EntityNameResolverComponent]]] = {
            "en": {
                "LANGUAGE": {
                    "full": EnglishLanguageNameResolver(),
                    "short": EnglishLanguageNameResolver(),
                    "pronoun": EntityNameListResolver(["the language"]),
                },
                "NEWSPAPER": {
                    "full": MultilingualNewspaperNameResolver(),
                    "short": MultilingualNewspaperNameResolver(),
                    "pronoun": MultilingualNewspaperNameResolver(),
                },
                "NAME": {
                    "full": MultilingualEntityNameResolver(),
                    "short": MultilingualEntityNameResolver(),
                    "pronoun": MultilingualEntityNameResolver(),
                },
            },
            "fr": {
                "LANGUAGE": {
                    "full": FrenchLanguageNameResolver(),
                    "short": FrenchLanguageNameResolver(),
                    "pronoun": FrenchLanguageNameResolver(),
                },
                "NEWSPAPER": {
                    "full": MultilingualNewspaperNameResolver(),
                    "short": MultilingualNewspaperNameResolver(),
                    "pronoun": MultilingualNewspaperNameResolver(),
                },
                "NAME": {
                    "full": MultilingualEntityNameResolver(),
                    "short": MultilingualEntityNameResolver(),
                    "pronoun": MultilingualEntityNameResolver(),
                },
            },
            "de": {
                "LANGUAGE": {
                    "full": GermanLanguageNameResolver(),
                    "short": GermanLanguageNameResolver(),
                    "pronoun": GermanLanguageNameResolver(),
                },
                "NEWSPAPER": {
                    "full": MultilingualNewspaperNameResolver(),
                    "short": MultilingualNewspaperNameResolver(),
                    "pronoun": MultilingualNewspaperNameResolver(),
                },
                "NAME": {
                    "full": MultilingualEntityNameResolver(),
                    "short": MultilingualEntityNameResolver(),
                    "pronoun": MultilingualEntityNameResolver(),
                },
            },
            "fi": {
                "LANGUAGE": {
                    "full": FinnishLanguageNameResolver(),
                    "short": FinnishLanguageNameResolver(),
                    "pronoun": FinnishLanguageNameResolver(),
                },
                "NEWSPAPER": {
                    "full": MultilingualNewspaperNameResolver(),
                    "short": MultilingualNewspaperNameResolver(),
                    "pronoun": MultilingualNewspaperNameResolver(),
                },
                "NAME": {
                    "full": MultilingualEntityNameResolver(),
                    "short": MultilingualEntityNameResolver(),
                    "pronoun": MultilingualEntityNameResolver(),
                },
            },
        }

    def is_entity(self, maybe_entity: Any) -> bool:
        if not isinstance(maybe_entity, str):
            log.debug("Value {} is not an entity".format(maybe_entity))
            return False
        return self._matcher.fullmatch(maybe_entity) is not None

    def parse_entity(self, entity: str) -> Tuple[str, str]:
        match = self._matcher.fullmatch(entity)
        if not match:
            raise ValueError("Value {} does not match entity regex".format(entity))
        if not len(match.groups()) == 2:
            raise Exception("Invalid number of matched groups?!")
        return match.groups()[0], match.groups()[1]

    def resolve_surface_form(
        self, registry: Registry, random: Generator, language: str, slot: Slot, entity: str, entity_type: str
    ) -> None:
        realizer = self.realizers.get(language, {}).get(entity_type, {}).get(slot.attributes.get("name_type"))
        if realizer is None:
            log.error(
                "No entity name resolver component for language {} and entity_type {}!".format(language, entity_type)
            )
            return

        realization = realizer.resolve(random, entity)
        slot.value = lambda x: realization
        log.debug('Realizer entity "{}" of type "{}" as "{}"'.format(entity, entity_type, realization))


class EntityNameResolverComponent(ABC):
    @abstractmethod
    def resolve(self, random: Generator, entity: str) -> str:
        """ Must be implemented in subclass. """


class EntityNameListResolver(EntityNameResolverComponent):
    def __init__(self, variants: List[str]) -> None:
        self.variants = variants

    def resolve(self, random: Generator, entity: str) -> str:
        return random.choice(self.variants)


class EntityNameDictionaryResolver(EntityNameResolverComponent):
    def __init__(self, dictionary: Dict[str, str]) -> None:
        self.dictionary = dictionary

    def resolve(self, random: Generator, entity: str) -> str:
        return self.dictionary.get(entity, "UNKNOWN-ENTITY:{}".format(entity))


class EnglishLanguageNameResolver(EntityNameDictionaryResolver):
    def __init__(self):
        from reporter.resources.language_name_resource import ENGLISH

        super().__init__(ENGLISH)


class FrenchLanguageNameResolver(EntityNameDictionaryResolver):
    def __init__(self):
        from reporter.resources.language_name_resource import FRENCH

        super().__init__(FRENCH)


class GermanLanguageNameResolver(EntityNameDictionaryResolver):
    def __init__(self):
        from reporter.resources.language_name_resource import GERMAN

        super().__init__(GERMAN)


class FinnishLanguageNameResolver(EntityNameDictionaryResolver):
    def __init__(self):
        from reporter.resources.language_name_resource import FINNISH

        super().__init__(FINNISH)


class MultilingualNewspaperNameResolver(EntityNameResolverComponent):
    def resolve(self, random: Generator, entity: str) -> str:
        return entity.replace("_", " ").capitalize()


class MultilingualEntityNameResolver(EntityNameResolverComponent):
    def resolve(self, random: Generator, entity: str) -> str:
        return entity
