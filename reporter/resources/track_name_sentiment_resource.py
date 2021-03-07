import logging
from typing import List, Type, Dict, Tuple

from reporter.core.models import Fact, Message
from reporter.core.realize_slots import RegexRealizer, SlotRealizerComponent
from reporter.newspaper_message_generator import TaskResult
from reporter.resources.processor_resource import ProcessorResource

log = logging.getLogger("root")


TEMPLATE = """
en: between {timestamp_from} and {timestamp_to}, {result_key} {result_value} {analysis_id}
| analysis_type = TrackNameSentiment:MinMaxMean
"""


class TrackNameSentimentResource(ProcessorResource):
    def templates_string(self) -> str:
        return TEMPLATE

    def parse_messages(self, task_result: TaskResult, context: List[TaskResult], language: str) -> List[Message]:

        language = language.split("-")[0]

        if not task_result.processor == "TrackNameSentiment":
            return []

        corpus, corpus_type = self.build_corpus_fields(task_result)

        entries: Dict[str, Dict[int, Tuple[float, float]]] = {}
        for entity in task_result.task_result["result"]:
            print("ENTITY:", entity)
            entity_name_map: Dict[str, str] = task_result.task_result["result"][entity].get("names", {})
            entity_name_priority_list = [
                entity_name_map.get(language, None),
                entity_name_map.get("en", None),
                list(entity_name_map.values())[0] if list(entity_name_map.values()) else None,
                entity,
            ]
            name = next(name for name in entity_name_priority_list if name)

            years: Dict[int, Tuple[float, float]] = {}
            for year in task_result.task_result["result"][entity]:
                if year == "names":
                    # Skip the names-map
                    continue
                sentiment = task_result.task_result["result"][entity][year]
                interestingness = task_result.task_result["interestingness"][entity][year]
                if sentiment != 0 or interestingness != 0:
                    years[int(year)] = (sentiment, interestingness)

            entries[name] = years

        messages: List[Message] = []

        for entry, years in entries.items():
            if not years:
                continue
            max_interestingness = max(interestingness for (year, (sentiment, interestingness)) in years.items())
            max_sentiment, max_sentiment_year = max(
                (sentiment, year) for (year, (sentiment, interestingness)) in years.items()
            )
            min_sentiment, min_sentiment_year = min(
                (sentiment, year) for (year, (sentiment, interestingness)) in years.items()
            )
            mean_sentiment = sum(sentiment for (year, (sentiment, interestingness)) in years.items()) / len(years)
            min_year = min(years)
            max_year = max(years)
            year_count = len(years)

            messages.append(
                Message(
                    Fact(
                        corpus,
                        corpus_type,
                        min_year,
                        max_year,
                        "between_years",
                        "TrackNameSentiment:MinMaxMean",
                        "[ENTITY:NAME:{}]".format(entry),
                        "[TrackNameSentiment:MinMaxMean:{}:{}:{}:{}:{}:{}]".format(
                            year_count,
                            mean_sentiment,
                            max_sentiment,
                            max_sentiment_year,
                            min_sentiment,
                            min_sentiment_year,
                        ),
                        max_interestingness,
                        "[LINK:{}]".format(task_result.uuid),  # uuid
                    )
                )
            )

        return messages

    def slot_realizer_components(self) -> List[Type[SlotRealizerComponent]]:
        return [EnglishTrackNameSentimentMinMaxMeanRealizer]


class EnglishTrackNameSentimentMinMaxMeanRealizer(RegexRealizer):
    def __init__(self, registry):
        super().__init__(
            registry,
            "en",
            r"\[TrackNameSentiment:MinMaxMean:([^:\]]+):([^:\]]+):([^:\]]+):([^:\]]+):([^:\]]+):([^:\]]+)\]",
            (1, 2, 3, 4, 5, 6),
            "was discussed during {} distinct years. The mean sentiment towards it was {} , "
            + "with the most positive sentiment ( {} ) occuring at {} "
            + "and the most negative sentiment ( {} ) occuring at {}",
        )
