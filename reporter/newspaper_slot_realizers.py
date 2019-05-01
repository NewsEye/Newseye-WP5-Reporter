
import logging

from reporter.core import RegexRealizer

log = logging.getLogger('root')

class EnglishFormatRealizer(RegexRealizer):

    def __init__(self):
        super().__init__(
            'en',
            r'\[format:([^\]]+)\]',
            1,
            'in the format "{}"'
        )

class EnglishLanguageRealizer(RegexRealizer):

    def __init__(self):
        super().__init__(
            'en',
            r'\[language_ssim:([^\]]+)\]',
            1,
            'in the {} language'
        )

class EnglishCategoryRealizer(RegexRealizer):

    def __init__(self):
        super().__init__(
            'en',
            r'\[lc_1letter_ssim:\w - ([^\]]+)\]',
            1,
            'from the category "{}"'
        )

class EnglishGeoRealizer(RegexRealizer):

    def __init__(self):
        super().__init__(
            'en',
            r'\[subject_geo_ssim:([^\]]+)\]',
            1,
            'about the location "{}"'
        )

class EnglishTopicRealizer(RegexRealizer):

    def __init__(self):
        super().__init__(
            'en',
            r'\[TOPIC:([^\]]+)\]',
            1,
            'about the topic "{}"'
        )

class EnglishPubdateRealizer(RegexRealizer):

    def __init__(self):
        super().__init__(
            'en',
            r'\[pub_date_ssim:([^\]]+)\]',
            1,
            'published in {}'
        )

class EnglishSubjectRealizer(RegexRealizer):

    def __init__(self):
        super().__init__(
            'en',
            r'\[subject_ssim:([^\]]+)\]',
            1,
            'about the subject "{}"'
        )

class EnglishSubjectEraRealizer(RegexRealizer):

    def __init__(self):
        super().__init__(
            'en',
            r'\[subject_era_ssim:([^\]]+)\]',
            1,
            'about the {}'
        )