
import logging

from reporter.core import RegexRealizer

log = logging.getLogger('root')

class EnglishFormatRealizer(RegexRealizer):

    def __init__(self, registry):
        super().__init__(
            registry,
            'en',
            r'\[has_model_ssim:([^\]]+)\]',
            1,
            'the format "{}"'
        )

class EnglishLanguageRealizer(RegexRealizer):

    def __init__(self, registry):
        super().__init__(
            registry,
            'en',
            r'\[language_ssi:([^\]]+)\]',
            1,
            '[ENTITY:LANGUAGE:{}]'
        )


class EnglishTopicRealizer(RegexRealizer):

    def __init__(self, registry):
        super().__init__(
            registry,
            'en',
            r'\[TOPIC:([^\]]+)\]',
            1,
            'the topic "{}"'
        )

class EnglishWordRealizer(RegexRealizer):

    def __init__(self, registry):
        super().__init__(
            registry,
            'en',
            r'\[WORD:([^\]]+)\]',
            1,
            'the word "{}"'
        )

class EnglishPubDateRealizer(RegexRealizer):

    def __init__(self, registry):
        super().__init__(
            registry,
            'en',
            r'\[date_created_dtsi:([^\]]+)\]',
            1,
            'published on [ENTITY:DATE:{}]'
        )

class EnglishPubYearRealizer(RegexRealizer):

    def __init__(self, registry):
        super().__init__(
            registry,
            'en',
            r'\[PUB_YEAR:([^\]]+)\]',
            1,
            (
                'published during {}',
                'published during the year {}',
                'published in {}',
            )
        )

class EnglishNewsPaperNameRealizer(RegexRealizer):

    def __init__(self, registry):
        super().__init__(
            registry,
            'en',
            r'\[member_of_collection_ids_ssim:([^\]]+)\]',
            1,
            'published in [ENTITY:NEWSPAPER:{}]'
        )

class EnglishYearRealizer(RegexRealizer):

    def __init__(self, registry):
        super().__init__(
            registry,
            'en',
            r'\[year(?:_isi):([^\]]+)\]',
            1,
            (
                'during {}',
                'during the year {}',
                'in {}',
            )
        )

class EnglishChangeRealizerIncrease(RegexRealizer):

    def __init__(self, registry):
        super().__init__(
            registry,
            'en',
            r'\[CHANGE:([^\]:]+):([^\]:]+)\]',
            (1, 2),
            (
                'increased from {} IPM to {}',
                'rose from {} IPM to {}',
            ),
            lambda before, after: float(before) < float(after)
        )


class EnglishChangeRealizerDecrease(RegexRealizer):

    def __init__(self, registry):
        super().__init__(
            registry,
            'en',
            r'\[CHANGE:([^\]:]+):([^\]:]+)\]',
            (1, 2),
            (
                'decreased from {} IPM {} ',
                'fell from {} IPM to {}',
            ),
            lambda before, after: float(before) > float(after)
        )

class EnglishQueryRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            'en',
            r'\[q:([^\]:]+)\]',
            1,
            '"{}"'
        )

# TODO: All Finnish language formats are not yet tested

class FinnishFormatRealizer(RegexRealizer):

    def __init__(self, registry):
        super().__init__(
            registry,
            'fi',
            r'\[format:([^\]]+)\]',
            1,
            '"{}"-muodossa'
        )

class FinnishLanguageRealizer(RegexRealizer):

    def __init__(self, registry):
        super().__init__(
            registry,
            'fi',
            r'\[language_ssi:([^\]]+)\]',
            1,
            'kielellä {}'
        )

class FinnishCategoryRealizer(RegexRealizer):

    def __init__(self, registry):
        super().__init__(
            registry,
            'fi',
            r'\[lc_1letter_ssim:\w - ([^\]]+)\]',
            1,
            'kategoriassa "{}"'
        )

class FinnishGeoRealizer(RegexRealizer):

    def __init__(self, registry):
        super().__init__(
            registry,
            'fi',
            r'\[subject_geo_ssim:([^\]]+)\]',
            1,
            'paikassa "{}"'
        )

class FinnishTopicRealizer(RegexRealizer):

    def __init__(self, registry):
        super().__init__(
            registry,
            'fi',
            r'\[TOPIC:([^\]]+)\]',
            1,
            'aiheeseen "{}"'
        )

class FinnishWordRealizer(RegexRealizer):

    def __init__(self, registry):
        super().__init__(
            registry,
            'fi',
            r'\[WORD:([^\]]+)\]',
            1,
            'sanaan "{}"'
        )

class FinnishPubdateRealizer(RegexRealizer):

    def __init__(self, registry):
        super().__init__(
            registry,
            'fi',
            r'\[pub_date_ssim:([^\]]+)\]',
            1,
            'julkaistu {}'
        )

class FinnishSubjectRealizer(RegexRealizer):

    def __init__(self, registry):
        super().__init__(
            registry,
            'fi',
            r'\[subject_ssim:([^\]]+)\]',
            1,
            'aiheesta "{}"'
        )

class FinnishSubjectEraRealizer(RegexRealizer):

    def __init__(self, registry):
        super().__init__(
            registry,
            'fi',
            r'\[subject_era_ssim:([^\]]+)\]',
            1,
            '{}'
        )


class FinnishYearRealizer(RegexRealizer):

    def __init__(self, registry):
        super().__init__(
            registry,
            'fi',
            r'\[year:([^\]]+)\]',
            1,
            (
                'vuonna {}',
                'vuoden {} aikana',
            )
        )

class FinnishChangeRealizerIncrease(RegexRealizer):

    def __init__(self, registry):
        super().__init__(
            registry,
            'fi',
            r'\[CHANGE:([^\]:]+):([^\]:]+)\]',
            (1, 2),
            (
                'kasvoi {} esiintymästä miljoonassa {}:ään ',
                'nousi {} esiintymästä miljoonassa {}:ään ',
            ),
            lambda before, after: float(before) < float(after)
        )


class FinnishChangeRealizerDecrease(RegexRealizer):

    def __init__(self, registry):
        super().__init__(
            registry,
            'fi',
            r'\[CHANGE:([^\]:]+):([^\]:]+)\]',
            (1, 2),
            (
                'laski {} esiintymästä miljoonassa {}:ään ',
                'putosi {} esiintymästä miljoonassa {}:ään ',
                'tippui {} esiintymästä miljoonassa {}:ään ',
            ),
            lambda before, after: float(before) > float(after)
        )

class FinnishQueryRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            'fi',
            r'\[q:([^\]:]+)\]',
            1,
            '"{}"'
        )


# TODO: All German language formats are not yet tested

class GermanFormatRealizer(RegexRealizer):

    def __init__(self, registry):
        super().__init__(
            registry,
            'de',
            r'\[format:([^\]]+)\]',
            1,
            'im Format "{}"'
        )

class GermanLanguageRealizer(RegexRealizer):

    def __init__(self, registry):
        super().__init__(
            registry,
            'de',
            r'\[language_ssi:([^\]]+)\]',
            1,
            '{} Sprache'
        )

class GermanCategoryRealizer(RegexRealizer):

    def __init__(self, registry):
        super().__init__(
            registry,
            'de',
            r'\[lc_1letter_ssim:\w - ([^\]]+)\]',
            1,
            'der Kategorie "{}"'
        )

class GermanGeoRealizer(RegexRealizer):

    def __init__(self, registry):
        super().__init__(
            registry,
            'de',
            r'\[subject_geo_ssim:([^\]]+)\]',
            1,
            'der Standort "{}"'
        )

class GermanTopicRealizer(RegexRealizer):

    def __init__(self, registry):
        super().__init__(
            registry,
            'de',
            r'\[TOPIC:([^\]]+)\]',
            1,
            'das Thema "{}"'
        )

class GermanWordRealizer(RegexRealizer):

    def __init__(self, registry):
        super().__init__(
            registry,
            'de',
            r'\[WORD:([^\]]+)\]',
            1,
            'das Wort "{}"'
        )

class GermanPubdateRealizer(RegexRealizer):

    def __init__(self, registry):
        super().__init__(
            registry,
            'de',
            r'\[pub_date_ssim:([^\]]+)\]',
            1,
            '{}'
        )

class GermanSubjectRealizer(RegexRealizer):

    def __init__(self, registry):
        super().__init__(
            registry,
            'de',
            r'\[subject_ssim:([^\]]+)\]',
            1,
            'über das Thema "{}"'
        )

class GermanSubjectEraRealizer(RegexRealizer):

    def __init__(self, registry):
        super().__init__(
            registry,
            'de',
            r'\[subject_era_ssim:([^\]]+)\]',
            1,
            '{}'
        )


class GermanYearRealizer(RegexRealizer):

    def __init__(self, registry):
        super().__init__(
            registry,
            'de',
            r'\[year:([^\]]+)\]',
            1,
            (
                'während des Jahres {}',
                'im Jahre {}',
            )
        )

class GermanChangeRealizerIncrease(RegexRealizer):

    def __init__(self, registry):
        super().__init__(
            registry,
            'de',
            r'\[CHANGE:([^\]:]+):([^\]:]+)\]',
            (1, 2),
            (
                'erhöht von {} IPM auf {}',
            ),
            lambda before, after: float(before) < float(after)
        )


class GermanChangeRealizerDecrease(RegexRealizer):

    def __init__(self, registry):
        super().__init__(
            registry,
            'de',
            r'\[CHANGE:([^\]:]+):([^\]:]+)\]',
            (1, 2),
            (
                'von {} auf {} IPM verringert',
            ),
            lambda before, after: float(before) > float(after)
        )

class GermanQueryRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            'de',
            r'\[q:([^\]:]+)\]',
            1,
            '"{}"'
        )