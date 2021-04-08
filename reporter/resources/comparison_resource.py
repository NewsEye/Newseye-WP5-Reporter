import logging
from typing import List, Type, Tuple

from reporter.core.models import Fact, Message
from reporter.core.realize_slots import RegexRealizer, SlotRealizerComponent, ListRegexRealizer
from reporter.newspaper_message_generator import TaskResult, WrongResourceException
from reporter.resources.processor_resource import ProcessorResource

log = logging.getLogger("root")


TEMPLATE = """
en: the {result_key} results of {corpus} differ with {"[Tooltip:JSD]"} of {result_value} {analysis_id}
fi: {corpus} {result_key} tulosten Jensen-Shannon eroavuus oli {result_value} {analysis_id}
de: Die Resultate für die {result_key} für {corpus} unterscheiden sich um eine Jensen-Shannon-Divergenz von {result_value} {analysis_id}
fr: Les résultats {result_key} {corpus} diffèrent avec une divergence Jensen-Shannon (JSD) de {result_value} {analysis_id}
| analysis_type = Compare:JSD

en: {corpus} are the most divergent for the {result_key} value {result_value} {analysis_id}
fi: {corpus} erosivat eniten {result_key} arvon {result_value} osalta {analysis_id}
de: {corpus} unterscheiden sich in der {result_key} am meisten für den Wert {result_value} {analysis_id}
fr: {corpus} diffèrent le plus pour la valeur {result_key} {result_value} {analysis_id}
| analysis_type = Compare:Most:Single

en: {corpus} are the most divergent for the {result_key} values {result_value} {analysis_id}
fi: {corpus} erosivat eniten {result_key} arvojen {result_value} osalta {analysis_id}
de: {corpus} unterscheiden sich in der {result_key} am meisten für die Werte {result_value} {analysis_id}
fr: {corpus} diffèrent le plus pour les valeurs {result_key} {result_value} {analysis_id}
| analysis_type = Compare:Most:Multi

en: {corpus} are the least divergent for the {result_key} value {result_value} {analysis_id}
fi: {corpus} erosivat vähiten {result_key} arvon {result_value} osalta {analysis_id}
de: {corpus} unterscheiden sich in der {result_key} am wenigsten für den Wert {result_value} {analysis_id}
fr: {corpus} diffèrent le moins pour la valeur {result_key} {result_value} {analysis_id}
| analysis_type = Compare:Least:Single

en: {corpus} are the least divergent for the {result_key} values {result_value} {analysis_id}
fi: {corpus} erosivat vähiten {result_key} arvojen {result_value} osalta {analysis_id}
de: {corpus} unterscheiden sich in der {result_key} am wenigsten für die Werte {result_value} {analysis_id}
fr: {corpus} diffèrent le moins pour les valeurs {result_key} {result_value} {analysis_id}
| analysis_type = Compare:Least:Multi

en: {corpus} have only a single shared {result_key} value: {result_value} {analysis_id}
fi: {corpus} omaavat vain yhden jaetun {result_key} arvon: {result_value} osalta {analysis_id}
de: {corpus} haben für die {result_key} nur einen gemeinsamen Wert: {result_value} {analysis_id}
fr: {corpus} ne partagent qu'une seule valeur {result_key}: {result_value} {analysis_id}
| analysis_type = Compare:Single

en: {corpus} have no shared {result_key} values {analysis_id}
fi: {corpus} eivät omaa yhtään jaettua {result_key} arvoa {analysis_id}
de: {corpus} haben für die {result_key} keine gemeinsamen Werte {analysis_id}
fr: {corpus} n'ont pas de valeurs {result_key} communes.
| analysis_type = Compare:None
"""  # noqa: E501


class ComparisonResource(ProcessorResource):
    def templates_string(self) -> str:
        return TEMPLATE

    @staticmethod
    def _jsd_message_parser(
        task_result: TaskResult, corpus: str, corpus_type: str, input_processor: str
    ) -> List[Message]:
        jsd = task_result.task_result["result"]["jensen_shannon_divergence"]
        interestingness = task_result.task_result["interestingness"]["jensen_shannon_divergence"]

        return [
            Message(
                Fact(
                    corpus,
                    corpus_type,
                    None,
                    None,
                    "all_time",
                    "Compare:JSD",
                    f"[Comparison:Processor:{input_processor}]",
                    jsd,
                    interestingness,
                    f"[LINK:{task_result.uuid}]",
                )
            )
        ]

    @staticmethod
    def _value_divergence_parser(
        task_result: TaskResult, corpus: str, corpus_type: str, input_processor: str
    ) -> List[Message]:

        # Obtain the result key that is *not* JSD (e.g. abs_diff)
        comparison_type = ""
        for val in task_result.task_result["result"]:
            if val != "jensen_shannon_divergence":
                comparison_type = val

        combined: List[Tuple[str, float, float]] = [
            (
                key,
                task_result.task_result["result"][comparison_type][key],
                task_result.task_result["interestingness"][comparison_type][key],
            )
            for key in task_result.task_result["result"][comparison_type]
        ]

        if len(combined) == 0:
            return [
                Message(
                    Fact(
                        corpus,
                        corpus_type,
                        None,
                        None,
                        "all_time",
                        "Compare:None",
                        f"[Comparison:Processor:{input_processor}]",
                        None,
                        task_result.task_result["interestingness"]["overall"],
                        f"[LINK:{task_result.uuid}]",
                    )
                )
            ]

        # Sort from least divergent to most divergent
        combined.sort(key=lambda x: x[1])
        messages: List[Message] = []

        if len(combined) == 1:
            key, val, interestingness = combined[0]
            messages.append(
                Message(
                    Fact(
                        corpus,
                        corpus_type,
                        None,
                        None,
                        "all_time",
                        "Compare:Single",
                        f"[Comparison:Processor:{input_processor}]",
                        f"[Comparison:Value:{key}:{comparison_type}:{val}]",
                        interestingness,
                        f"[LINK:{task_result.uuid}]",
                    )
                )
            )

        elif len(combined) <= 3:
            (key, val, interestingness) = combined[0]
            messages.append(
                Message(
                    Fact(
                        corpus,
                        corpus_type,
                        None,
                        None,
                        "all_time",
                        "Compare:Least:Single",
                        f"[Comparison:Processor:{input_processor}]",
                        f"[Comparison:Value:{key}:{comparison_type}:{val}]",
                        interestingness,
                        f"[LINK:{task_result.uuid}]",
                    )
                )
            )
            (key, val, interestingness) = combined[1]
            messages.append(
                Message(
                    Fact(
                        corpus,
                        corpus_type,
                        None,
                        None,
                        "all_time",
                        "Compare:Most:Single",
                        f"[Comparison:Processor:{input_processor}]",
                        f"[Comparison:Value:{key}:{comparison_type}:{val}]",
                        interestingness,
                        f"[LINK:{task_result.uuid}]",
                    )
                )
            )

        else:  # at least four keys
            count = min(3, len(combined) // 2)  # half-and-half, ignore middle value if odd n. Max 3 in any case.

            least_vals = combined[:count]
            least_vals_max_interestingness = max(interestingness for (_, _, interestingness) in least_vals)
            messages.append(
                Message(
                    Fact(
                        corpus,
                        corpus_type,
                        None,
                        None,
                        "all_time",
                        "Compare:Least:Multi",
                        f"[Comparison:Processor:{input_processor}]",
                        "[Comparison:ValueList:{}]".format(
                            "|".join(["{}:{}:{}".format(key, comparison_type, value) for (key, value, _) in least_vals])
                        ),
                        least_vals_max_interestingness,
                        f"[LINK:{task_result.uuid}]",
                    )
                )
            )
            most_vals = combined[-count:]
            most_vals_max_interestingness = max(interestingness for (_, _, interestingness) in most_vals)
            messages.append(
                Message(
                    Fact(
                        corpus,
                        corpus_type,
                        None,
                        None,
                        "all_time",
                        "Compare:Most:Multi",
                        f"[Comparison:Processor:{input_processor}]",
                        "[Comparison:ValueList:{}]".format(
                            "|".join(["{}:{}:{}".format(key, comparison_type, value) for (key, value, _) in most_vals])
                        ),
                        most_vals_max_interestingness,
                        f"[LINK:{task_result.uuid}]",
                    )
                )
            )

        return messages

    def parse_messages(self, task_result: TaskResult, context: List[TaskResult], language: str) -> List[Message]:
        if not task_result.processor == "Comparison":
            raise WrongResourceException()

        messages: List[Message] = []

        corpus, corpus_type = self.build_corpus_fields(task_result)
        input_processor = task_result.parameters["input_processor"]
        if input_processor == "ExtractFacets":
            input_processor += ":" + task_result.parameters["facet"]

        messages += self._jsd_message_parser(task_result, corpus, corpus_type, input_processor)
        messages += self._value_divergence_parser(task_result, corpus, corpus_type, input_processor)

        return messages

    def slot_realizer_components(self) -> List[Type[SlotRealizerComponent]]:
        return [
            GenericInputProcessorRealizer,
            ExtractFacetsInputProcessorRealizer,
            #
            EnglishComparisonValueListRealizer,
            EnglishComparisonValueRealizer,
            EnglishComparisonTypeAbsDiffRealizer,
            #
            FinnishComparisonValueListRealizer,
            FinnishComparisonValueRealizer,
            FinnishComparisonTypeAbsDiffRealizer,
            #
            GermanComparisonValueListRealizer,
            GermanComparisonValueRealizer,
            GermanComparisonTypeAbsDiffRealizer,
            #
            FrenchComparisonValueListRealizer,
            FrenchComparisonValueRealizer,
            FrenchComparisonTypeAbsDiffRealizer,
        ]


class GenericInputProcessorRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry, "ANY", r"\[Comparison:Processor:([^:\]]+)\]", [1], "{}",
        )


class ExtractFacetsInputProcessorRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry, "ANY", r"\[Comparison:Processor:ExtractFacets:([^:\]]+)\]", [1], "ExtractFacet ({})",
        )


class EnglishComparisonValueListRealizer(ListRegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry, "en", r"\[Comparison:ValueList:([^\]]+)\]", 1, "[Comparison:Value:{}]", "and",
        )


class EnglishComparisonValueRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "en",
            r"\[Comparison:Value:([^\]]+):([^\]]+):([^\]]+)\]",
            [1, 2, 3],
            "{} ( [Comparison:ComparisonType:{}] = {} )",
        )


class EnglishComparisonTypeAbsDiffRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry, "en", r"\[Comparison:ComparisonType:abs_diff\]", [], "absolute difference",
        )


class FinnishComparisonValueListRealizer(ListRegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry, "fi", r"\[Comparison:ValueList:([^\]]+)\]", 1, "[Comparison:Value:{}]", "ja",
        )


class FinnishComparisonValueRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "fi",
            r"\[Comparison:Value:([^\]]+):([^\]]+):([^\]]+)\]",
            [1, 2, 3],
            "'{}' ( [Comparison:ComparisonType:{}] = {} )",
        )


class FinnishComparisonTypeAbsDiffRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry, "fi", r"\[Comparison:ComparisonType:abs_diff\]", [], "absoluuttinen eroavaisuus",
        )


class GermanComparisonValueListRealizer(ListRegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry, "de", r"\[Comparison:ValueList:([^\]]+)\]", 1, "[Comparison:Value:{}]", "und",
        )


class GermanComparisonValueRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "de",
            r"\[Comparison:Value:([^\]]+):([^\]]+):([^\]]+)\]",
            [1, 2, 3],
            "'{}' ( [Comparison:ComparisonType:{}] = {} )",
        )


class GermanComparisonTypeAbsDiffRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry, "de", r"\[Comparison:ComparisonType:abs_diff\]", [], "absolute Differenz",
        )


class FrenchComparisonValueListRealizer(ListRegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry, "fr", r"\[Comparison:ValueList:([^\]]+)\]", 1, "[Comparison:Value:{}]", "et",
        )


class FrenchComparisonValueRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "fr",
            r"\[Comparison:Value:([^\]]+):([^\]]+):([^\]]+)\]",
            [1, 2, 3],
            "'{}' ( [Comparison:ComparisonType:{}] = {} )",
        )


class FrenchComparisonTypeAbsDiffRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry, "fr", r"\[Comparison:ComparisonType:abs_diff\]", [], "différence absolue",
        )
