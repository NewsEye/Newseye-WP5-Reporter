
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


class EnglishCollectionNameRealizer(RegexRealizer):

    def __init__(self, registry):
        super().__init__(
            registry,
            'en',
            r'\[member_of_collection_ids_ssim:([^\]]+)\]',
            1,
            '[ENTITY:NEWSPAPER:{}]'
        )

class EnglishNewspaperNameRealizer(RegexRealizer):

    def __init__(self, registry):
        super().__init__(
            registry,
            'en',
            r'\[NEWSPAPER_NAME:([^\]]+)\]',
            1,
            'published in [ENTITY:NEWSPAPER:{}]'
        )

class EnglishYearRealizer(RegexRealizer):

    def __init__(self, registry):
        super().__init__(
            registry,
            'en',
            r'\[year:([^\]]+)\]',
            1,
            (
                'during {}',
                'during the year {}',
                'in {}',
            )
        )

class EnglishYearIsiRealizer(RegexRealizer):

    def __init__(self, registry):
        super().__init__(
            registry,
            'en',
            r'\[year_isi:([^\]]+)\]',
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
            r'\[has_model_ssim:([^\]]+)\]',
            1,
            '"{}"'
        )

class FinnishLanguageRealizer(RegexRealizer):

    def __init__(self, registry):
        super().__init__(
            registry,
            'fi',
            r'\[language_ssi:([^\]]+)\]',
            1,
            '[ENTITY:LANGUAGE:{}]'
        )


class FinnishTopicRealizer(RegexRealizer):

    def __init__(self, registry):
        super().__init__(
            registry,
            'fi',
            r'\[TOPIC:([^\]]+)\]',
            1,
            'aiheeseen "{}" liittyvää'
        )

class FinnishWordRealizer(RegexRealizer):

    def __init__(self, registry):
        super().__init__(
            registry,
            'fi',
            r'\[WORD:([^\]]+)\]',
            1,
            'sanan "{}" sisältävää'
        )

class FinnishPubDateRealizer(RegexRealizer):

    def __init__(self, registry):
        super().__init__(
            registry,
            'fi',
            r'\[date_created_dtsi:([^\]]+)\]',
            1,
            '[ENTITY:DATE:{}]'
        )

class FinnishPubYearRealizer(RegexRealizer):

    def __init__(self, registry):
        super().__init__(
            registry,
            'fi',
            r'\[PUB_YEAR:([^\]]+)\]',
            1,
            'vuonna {} julkaistua',
        )


class FinnishCollectionNameRealizer(RegexRealizer):

    def __init__(self, registry):
        super().__init__(
            registry,
            'fi',
            r'\[member_of_collection_ids_ssim:([^\]]+)\]',
            1,
            '[ENTITY:NEWSPAPER:{}]'
        )

class FinnishNewspaperNameRealizer(RegexRealizer):

    def __init__(self, registry):
        super().__init__(
            registry,
            'fi',
            r'\[NEWSPAPER_NAME:([^\]]+)\]',
            1,
            'lehdessä [ENTITY:NEWSPAPER:{}] julkaistua'
        )

class FinnishYearRealizer(RegexRealizer):

    def __init__(self, registry):
        super().__init__(
            registry,
            'fi',
            r'\[year:([^\]]+)\]',
            1,
            '{}',
        )

class FinnishYearIsiRealizer(RegexRealizer):

    def __init__(self, registry):
        super().__init__(
            registry,
            'fi',
            r'\[year_isi:([^\]]+)\]',
            1,
            '{}',
        )

class FinnishChangeRealizerIncrease(RegexRealizer):

    def __init__(self, registry):
        super().__init__(
            registry,
            'fi',
            r'\[CHANGE:([^\]:]+):([^\]:]+)\]',
            (1, 2),
            (
                'kasvoi {} osumasta {} osumaan miljoonasta',
                'nousi {} osumasta {} osumaan miljoonassa',
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
                'laski {} osumasta {} osumaan miljoonasta',
                'putosi {} osumasta {} osumaan miljoonassa',
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