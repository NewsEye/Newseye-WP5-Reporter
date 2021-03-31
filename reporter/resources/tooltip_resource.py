import logging
from typing import List, Type

from reporter.core.models import Message
from reporter.core.realize_slots import SlotRealizerComponent, RegexRealizer
from reporter.newspaper_message_generator import TaskResult
from reporter.resources.processor_resource import ProcessorResource

log = logging.getLogger("root")


class TooltipResource(ProcessorResource):
    def templates_string(self) -> str:
        return ""

    def parse_messages(self, task_result: TaskResult, context: List[TaskResult], language: str) -> List[Message]:
        return []

    def slot_realizer_components(self) -> List[Type[SlotRealizerComponent]]:
        return [
            EnglishTMWeightTooltipRealizer,
            EnglishJensenShannonTooltipRealizer,
            EnglishJSDTooltipRealizer,
            EnglishDiceTooltipRealizer,
            EnglishSalienceTooltipRealizer,
            EnglishStanceTooltipRealizer,
            EnglishSentimentTooltipRealizer,
            EnglishTFIDFTooltipRealizer,
        ]


class TooltipRealizer(RegexRealizer):
    def __init__(self, registry, language, term, explanation, term_expression=None):
        self.term = term
        self.explanation = explanation
        self.term_expression = term_expression
        super().__init__(
            registry,
            language,
            fr"(.*)\[Tooltip:{self.term}\](.*)",
            [1, 2],
            rf'{{}}<abbr title="{self.explanation}">{self.term_expression if self.term_expression else self.term}</abbr>{{}}',  # noqa: E501
        )


class EnglishJSDTooltipRealizer(TooltipRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "ANY",
            "JSD",
            "The Jensen–Shannon divergence is a method of measuring the similarity between two probability "
            "distributions. The values range from 1 (distributions are identical) to 0 (distributions are completely "
            "different).",
        )


class EnglishJensenShannonTooltipRealizer(TooltipRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "ANY",
            "Jensen–Shannon divergence",
            "The Jensen–Shannon divergence is a method of measuring the similarity between two probability "
            "distributions. The values range from 1 (distributions are identical) to 0 (distributions are completely "
            "different).",
        )


class EnglishDiceTooltipRealizer(TooltipRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "ANY",
            "Dice",
            "The Sørensen–Dice coefficient is a statistic used to gauge the similarity of two samples. The values "
            "range from 1 (the samples are identical) to 0 (the samples are completely unrelated).",
        )


class EnglishTMWeightTooltipRealizer(TooltipRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "ANY",
            "TMWeight",
            "The weight of a topic describes the degree to which a document or a corpus discusses that topic. The "
            "values range from 1 (document only discusses this topic) to 0 (document does not discuss topic).",
            term_expression="weight",
        )


class EnglishStanceTooltipRealizer(TooltipRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "ANY",
            "stance",
            "Stance describes whether something is discussed in positive, neutral or negative terms. The values range "
            "from -1 (extremely negative) to 0 (neutral) to 1 (extremely positive).",
        )


class EnglishSentimentTooltipRealizer(TooltipRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "ANY",
            "sentiment",
            "Sentiment describes whether something is discussed in positive, neutral or negative terms. The values "
            "range from -1 (extremely negative) to 0 (neutral) to 1 (extremely positive).",
        )


class EnglishSalienceTooltipRealizer(TooltipRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "ANY",
            "salience",
            "Salience is an estimate of how important/relevant/prominent something is. Values range from 0 (not at "
            "all important) to 1 (extremely important).",
        )


class EnglishTFIDFTooltipRealizer(TooltipRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "ANY",
            "TF-IDF",
            "TF-IDF reflects how important a word is to a document or subcorpus. A word has a high TF-IDF if it is "
            "rare in the larger corpus, but common in the document/subcorpus.",
        )
