import logging
import re
import traceback

import requests
from typing import List, Tuple, Callable, Type

from reporter.core import RegexRealizer, SlotRealizerComponent, TemplateComponent, Slot, Registry
from reporter.constants import CONJUNCTIONS

log = logging.getLogger("root")


class AbstractTopicRealizer(SlotRealizerComponent):
    parser_regex = re.compile(r"\[TOPIC:([^\]]+):([^\]]+):([^\]]+)\]")

    def __init__(
        self,
        language: str,
        registry: Registry,
        backup_realizer_constructor: Type,
        template: str,
        value_order: Tuple[int, ...],
    ) -> None:
        self.registry = registry
        self.language = language
        self.backup_realizer = _BackupEnglishTopicRealizer(registry)
        self.template = template
        self.value_order = value_order

    def supported_languages(self) -> List[str]:
        return [self.language]

    def realize(self, slot: Slot) -> Tuple[bool, List[TemplateComponent]]:
        match = re.fullmatch(self.parser_regex, slot.value)
        if not match:
            return False, []
        model_type, model_name, topic_id = match.groups()
        try:
            response = requests.post(
                "https://newseye-wp4.cs.helsinki.fi/{}/describe-topic".format(model_type),
                json={"model_name": model_name, "topic_id": topic_id, "lang": self.language},
            )
            topic_words = response.json()["topic_desc"].split()
            conjunction = CONJUNCTIONS.get(self.language, {}).get("default_combiner")
            if conjunction:
                topic_description = '"{}" {} "{}"'.format(
                    '", "'.join(topic_words[:4]), conjunction, topic_words[4]
                )
            else:
                topic_description = '"{}"'.format('", "'.join(topic_words[:5]))
            print(topic_description)
            raw_values = [model_type.upper(), model_name.upper(), topic_id, topic_description]
            values = [raw_values[idx] for idx in self.value_order]
            string_realization = self.template.format(*values)
            log.debug("String realization: {}".format(string_realization))
            components = []
            for realization_token in string_realization.split():
                new_slot = slot.copy(include_fact=True)
                # An ugly hack that ensures the lambda correctly binds to the value of realization_token at this
                # time. Without this, all the lambdas bind to the final value of the realization_token variable, ie.
                # the final value at the end of the loop.  See https://stackoverflow.com/a/10452819
                new_slot.value = lambda f, realization_token=realization_token: realization_token
                components.append(new_slot)
            log.info("Components: {}".format([str(c) for c in components]))
            return True, components

        except Exception as ex:
            log.warning("Failed to fetch topic description: {}".format(ex))
            traceback.print_tb(ex.__traceback__)
            return self.backup_realizer.realize(slot)


class _BackupEnglishTopicRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "en",
            r"\[TOPIC:([^\]]+):([^\]]+):([^\]]+)\]",
            (3, 1, 2),
            'the topic "{}" of the {} topic model "{}"',
        )


class EnglishTopicRealizer(AbstractTopicRealizer):
    def __init__(self, registry):
        super().__init__(
            "en",
            registry,
            _BackupEnglishTopicRealizer,
            "the topic characterized by the words {} from the {} model {}",
            (3, 0, 1),  # 0 = model_type, 1 = model_name, 2 = topic_id, 3 = topic_desc
        )


class EnglishFormatRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "en", r"\[has_model_ssim:([^\]]+)\]", 1, 'the format "{}"')


class EnglishLanguageRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "en", r"\[language_ssi:([^\]]+)\]", 1, "[ENTITY:LANGUAGE:{}]")


class EnglishWordRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "en", r"\[WORD:([^\]]+)\]", 1, 'the word "{}"')


class EnglishPubDateRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry, "en", r"\[date_created_dtsi:([^\]]+)\]", 1, "published on [ENTITY:DATE:{}]"
        )


class EnglishPubYearRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "en",
            r"\[PUB_YEAR:([^\]]+)\]",
            1,
            ("published during {}", "published during the year {}", "published in {}"),
        )


class EnglishCollectionNameRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "en",
            r"\[member_of_collection_ids_ssim:([^\]]+)\]",
            1,
            "[ENTITY:NEWSPAPER:{}]",
        )


class EnglishNewspaperNameRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "en", r"\[NEWSPAPER_NAME:([^\]]+)\]", 1, "published in [ENTITY:NEWSPAPER:{}]")


class EnglishDocumentIdRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "en", r"\[DOCUMENT_ID:([^\]]+)\]", 1, "document with ID {}")


class EnglishYearRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry, "en", r"\[year:([^\]]+)\]", 1, ("during {}", "during the year {}", "in {}")
        )


class EnglishYearIsiRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "en",
            r"\[year_isi:([^\]]+)\]",
            1,
            ("during {}", "during the year {}", "in {}"),
        )


class EnglishChangeRealizerIncrease(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "en",
            r"\[CHANGE:([^\]:]+):([^\]:]+)\]",
            (1, 2),
            ("increased from {} items per million to {}", "rose from {} items per million to {}"),
            lambda before, after: float(before) < float(after),
        )


class EnglishChangeRealizerDecrease(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "en",
            r"\[CHANGE:([^\]:]+):([^\]:]+)\]",
            (1, 2),
            ("decreased from {} items per million {} ", "fell from {} items per million to {}"),
            lambda before, after: float(before) > float(after),
        )


class EnglishQueryRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "en", r"\[q:([^\]:]+)\]", 1, 'the query "{}"')


class EnglishQueryMmRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "en",
            r"\[q:([^\]:]+)\] \[mm:([^\]:]+)\]",
            (1, 2),
            'the query "{}" (min match = {})',
        )


class EnglishQueryMmFilterRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "en",
            r"\[q:([^\]:]+)\] \[mm:([^\]:]+)\] \[fq:([^\]]+)\]",
            (1, 2, 3),
            'the query "{}" (min match = {}) on data from [{}]',
        )


class EnglishQueryFilterRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "en",
            r"\[q:([^\]:]+)\] \[fq:([^\]]+)\]",
            (1, 2),
            'the query "{}" on data from [{}]',
        )


class EnglishTopicWeightRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "en", r"\[TOPIC_WEIGHT:([^\]:]+)\]", 1, "{}")


# TODO: All Finnish language formats are not yet tested
class FinnishFormatRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "fi", r"\[has_model_ssim:([^\]]+)\]", 1, '"{}"')


class FinnishLanguageRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "fi", r"\[language_ssi:([^\]]+)\]", 1, "[ENTITY:LANGUAGE:{}]")


class _BackupFinnishTopicRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "fi",
            r"\[TOPIC:([^\]]+):([^\]]+):([^\]]+)\]",
            (1, 2, 3),
            '{}-aihemallin "{}" aiheeseen "{}" liittyvä',
        )


class FinnishTopicRealizer(AbstractTopicRealizer):
    def __init__(self, registry):
        super().__init__(
            "fi",
            registry,
            _BackupFinnishTopicRealizer,
            "{}-aihemallin {} sanojen {} kuvaamaan aiheeseen",
            (0, 1, 3),  # 0 = model_type, 1 = model_name, 2 = topic_id, 3 = topic_desc
        )


class FinnishWordRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "fi", r"\[WORD:([^\]]+)\]", 1, 'sanan "{}" sisältävää')


class FinnishPubDateRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "fi", r"\[date_created_dtsi:([^\]]+)\]", 1, "[ENTITY:DATE:{}]")


class FinnishPubYearRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "fi", r"\[PUB_YEAR:([^\]]+)\]", 1, "vuonna {} julkaistua")


class FinnishCollectionNameRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "fi",
            r"\[member_of_collection_ids_ssim:([^\]]+)\]",
            1,
            "[ENTITY:NEWSPAPER:{}]",
        )


class FinnishNewspaperNameRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "fi",
            r"\[NEWSPAPER_NAME:([^\]]+)\]",
            1,
            "lehdessä [ENTITY:NEWSPAPER:{}] julkaistua",
        )


class FinnishDocumentIdRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "fi", r"\[DOCUMENT_ID:([^\]]+)\]", 1, "dokumenttiin, jonka ID on {}")


class FinnishYearRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "fi", r"\[year:([^\]]+)\]", 1, "{}")


class FinnishYearIsiRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "fi", r"\[year_isi:([^\]]+)\]", 1, "{}")


class FinnishChangeRealizerIncrease(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "fi",
            r"\[CHANGE:([^\]:]+):([^\]:]+)\]",
            (1, 2),
            (
                "kasvoi {} osumasta {} osumaan miljoonasta",
                "nousi {} osumasta {} osumaan miljoonassa",
            ),
            lambda before, after: float(before) < float(after),
        )


class FinnishChangeRealizerDecrease(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "fi",
            r"\[CHANGE:([^\]:]+):([^\]:]+)\]",
            (1, 2),
            (
                "laski {} osumasta {} osumaan miljoonasta",
                "putosi {} osumasta {} osumaan miljoonassa",
            ),
            lambda before, after: float(before) > float(after),
        )


class FinnishQueryRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "fi", r"\[q:([^\]:]+)\]", 1, '"{}"')


class FinnishQueryMmRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry, "fi", r"\[q:([^\]:]+)\] \[mm:([^\]:]+)\]", (1, 2), '"{}" (min match = {})'
        )


class FinnishQueryMmFilterRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "fi",
            r"\[q:([^\]:]+)\] \[mm:([^\]:]+)\] \[fq:([^\]]+)\]",
            (1, 2, 3),
            '"{}" (min match = {}) kohdistuen kokoelmaan [{}]',
        )


class FinnishQueryFilterRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "fi",
            r"\[q:([^\]:]+)\] \[fq:([^\]]+)\]",
            (1, 2),
            '"{}" kohdistuen kokoelmaan [{}]',
        )


class FinnishTopicWeightRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "fi", r"\[TOPIC_WEIGHT:([^\]:]+)\]", 1, "{}")


# TODO: All German language formats are not yet tested


class GermanFormatRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "de", r"\[has_model_ssim:([^\]]+)\]", 1, 'im Format "{}"')


class GermanLanguageRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry, "de", r"\[language_ssi:([^\]]+)\]", 1, "auf [ENTITY:LANGUAGE:{}]"
        )


class GermanGeoRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "de", r"\[subject_geo_ssim:([^\]]+)\]", 1, 'der Standort "{}"')


class _BackupGermanTopicRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "de",
            r"\[TOPIC:([^\]]+):([^\]]+):([^\]]+)\]",
            (3, 1, 2),
            'das Thema "{}" aus dem {} Modell "{}"',
        )


class GermanTopicRealizer(AbstractTopicRealizer):
    def __init__(self, registry):
        super().__init__(
            "de",
            registry,
            _BackupEnglishTopicRealizer,
            "das Thema, das durch die Wörter {} aus dem {} Modell {} gekennzeichnet ist",
            (3, 0, 1),  # 0 = model_type, 1 = model_name, 2 = topic_id, 3 = topic_desc
        )


class GermanWordRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "de", r"\[WORD:([^\]]+)\]", 1, 'das Wort "{}"')


class GermanPubDateRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "de",
            r"\[date_created_dtsi:([^\]]+)\]",
            1,
            "in [ENTITY:DATE:{}] veröffentlicht",
        )


class GermanPubYearRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "de", r"\[PUB_YEAR:([^\]]+)\]", 1, ("veröffentlicht im Jahr {}"))


class GermanCollectionNameRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "de",
            r"\[member_of_collection_ids_ssim:([^\]]+)\]",
            1,
            "[ENTITY:NEWSPAPER:{}]",
        )


class GermanNewspaperNameRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "de",
            r"\[NEWSPAPER_NAME:([^\]]+)\]",
            1,
            "in [ENTITY:NEWSPAPER:{}] veröffentlicht",
        )


class GermanDocumentIdRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "de", r"\[DOCUMENT_ID:([^\]]+)\]", 1, "Dokument mit der ID {}")


class GermanSubjectRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "de", r"\[subject_ssim:([^\]]+)\]", 1, 'über das Thema "{}"')


class GermanSubjectEraRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "de", r"\[subject_era_ssim:([^\]]+)\]", 1, "{}")


class GermanYearRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry, "de", r"\[year:([^\]]+)\]", 1, ("während des Jahres {}", "im Jahr {}")
        )


class GermanYearIsiRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "de", r"\[year_isi:([^\]]+)\]", 1, ("im Jahr {}"))


class GermanChangeRealizerIncrease(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "de",
            r"\[CHANGE:([^\]:]+):([^\]:]+)\]",
            (1, 2),
            ("stieg von {} Teile pro Million auf {}",),
            lambda before, after: float(before) < float(after),
        )


class GermanChangeRealizerDecrease(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "de",
            r"\[CHANGE:([^\]:]+):([^\]:]+)\]",
            (1, 2),
            ("verringerte sich von {} auf {} Teile pro Million",),
            lambda before, after: float(before) > float(after),
        )


class GermanQueryRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "de", r"\[q:([^\]:]+)\]", 1, '"{}"')


class GermanQueryMmRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "de",
            r"\[q:([^\]:]+)\] \[mm:([^\]:]+)\]",
            (1, 2),
            'die Abfrage "{}" (das Minimum Match = {})',
        )


class GermanQueryMmFilterRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "de",
            r"\[q:([^\]:]+)\] \[mm:([^\]:]+)\] \[fq:([^\]]+)\]",
            (1, 2, 3),
            'die Abfrage "{}" (das Minimum Match  = {}) nach Daten von [{}]',
        )


class GermanQueryFilterRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "de",
            r"\[q:([^\]:]+)\] \[fq:([^\]]+)\]",
            (1, 2),
            'die Abfrage "{}" nach Daten von [{}]',
        )


class GermanTopicWeightRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(registry, "de", r"\[TOPIC_WEIGHT:([^\]:]+)\]", 1, "{}")
