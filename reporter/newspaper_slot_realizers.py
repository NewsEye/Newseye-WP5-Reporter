
import logging

from reporter.core import RegexRealizer

log = logging.getLogger('root')

class EnglishFormatRealizer(RegexRealizer):

    def __init__(self, random):
        super().__init__(
            random,
            'en',
            r'\[format:([^\]]+)\]',
            1,
            'the format "{}"'
        )

class EnglishLanguageRealizer(RegexRealizer):

    def __init__(self, random):
        super().__init__(
            random,
            'en',
            r'\[language_ssim:([^\]]+)\]',
            1,
            'the {} language'
        )

class EnglishCategoryRealizer(RegexRealizer):

    def __init__(self, random):
        super().__init__(
            random,
            'en',
            r'\[lc_1letter_ssim:\w - ([^\]]+)\]',
            1,
            'the category "{}"'
        )

class EnglishGeoRealizer(RegexRealizer):

    def __init__(self, random):
        super().__init__(
            random,
            'en',
            r'\[subject_geo_ssim:([^\]]+)\]',
            1,
            'the location "{}"'
        )

class EnglishTopicRealizer(RegexRealizer):

    def __init__(self, random):
        super().__init__(
            random,
            'en',
            r'\[TOPIC:([^\]]+)\]',
            1,
            'the topic "{}"'
        )

class EnglishWordRealizer(RegexRealizer):

    def __init__(self, random):
        super().__init__(
            random,
            'en',
            r'\[WORD:([^\]]+)\]',
            1,
            'the word "{}"'
        )

class EnglishPubdateRealizer(RegexRealizer):

    def __init__(self, random):
        super().__init__(
            random,
            'en',
            r'\[pub_date_ssim:([^\]]+)\]',
            1,
            'published in {}'
        )

class EnglishSubjectRealizer(RegexRealizer):

    def __init__(self, random):
        super().__init__(
            random,
            'en',
            r'\[subject_ssim:([^\]]+)\]',
            1,
            'the subject "{}"'
        )

class EnglishSubjectEraRealizer(RegexRealizer):

    def __init__(self, random):
        super().__init__(
            random,
            'en',
            r'\[subject_era_ssim:([^\]]+)\]',
            1,
            '{}'
        )

class EnglishYearRealizer(RegexRealizer):

    def __init__(self, random):
        super().__init__(
            random,
            'en',
            r'\[year:([^\]]+)\]',
            1,
            (
                'during {}',
                'during the year {}',
                'in {}',
            )
        )

class EnglishChangeRealizerIncrease(RegexRealizer):

    def __init__(self, random):
        super().__init__(
            random,
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

    def __init__(self, random):
        super().__init__(
            random,
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
    def __init__(self, random):
        super().__init__(
            random,
            'en',
            r'\[q:([^\]:]+)\]',
            1,
            '"{}"'
        )