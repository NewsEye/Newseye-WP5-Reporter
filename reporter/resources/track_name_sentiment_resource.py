import logging
from functools import lru_cache
from time import sleep
from typing import List, Type, Dict, Tuple, Optional

import requests

from reporter.core.models import Fact, Message
from reporter.core.realize_slots import SlotRealizerComponent
from reporter.newspaper_message_generator import TaskResult, WrongResourceException
from reporter.resources.processor_resource import ProcessorResource

log = logging.getLogger("root")


TEMPLATE = """
en: the most negative {"[Tooltip:sentiment]"} towards {result_key} ( {result_value} ) occurred at {time} {analysis_id}
fi: suhtautuminen entiteettiin {result_key} oli kaikkein negatiivisin ( {result_value} ) {time} {analysis_id}
de: Die negativste Wertung zu {result_key} ( {result_value} ) trat {time} auf {analysis_id}
fr: le sentiment le plus négatif envers {result_key} ( {result_value} ) se rencontre en {time} {analysis_id}
| analysis_type = TrackNameSentiment:Min

en: the most positive {"[Tooltip:sentiment]"} towards {result_key} ( {result_value} ) occurred at {time} {analysis_id}
fi: suhtautuminen entiteettiin {result_key} oli kaikkein positiivisin ( {result_value} ) {time} {analysis_id}
de: de: Die positivste Wertung zu {result_key} ( {result_value} ) trat {time} auf {analysis_id}
fr: le sentiment le plus positif envers {result_key} ( {result_value} ) se rencontre en {time} {analysis_id}
| analysis_type = TrackNameSentiment:Max

en: the mean {"[Tooltip:sentiment]"} towards {result_key} {time} was {result_value} {analysis_id}
fi: keskimääräinen suhtautuminen entiteettiin {result_key} {time} oli {result_value} {analysis_id}
de: Die mittlere Wertung zu {result_key} {time} war {result_value}
fr: les sentiments moyens envers la {result_key} {time} étaient de {result_value} {analysis_id}
| analysis_type = TrackNameSentiment:Mean

en: {result_key} was discussed during {result_value} distinct years {time} {analysis_id}
fi: entiteetistä {result_key} keskusteltiin yhteensä {result_value} vuoden aikana {time} {analysis_id}
de: {result_key} wurde in {result_value} verschiedenen Jahren {time} diskutiert {analysis_id}
fr: {result_key} a été discutée pendant {result_value} années distinctes {time} {analysis_id}
| analysis_type = TrackNameSentiment:CountYears
"""  # noqa: E501


class TrackNameSentimentResource(ProcessorResource):
    def templates_string(self) -> str:
        return TEMPLATE

    @lru_cache(maxsize=256)
    def _resolve_name_from_solr(self, entity: str, language: str) -> Optional[str]:
        if not entity.startswith("entity_"):
            return None
        try:
            sleep(1)
            solr_query = f"http://newseye.cs.helsinki.fi:9985/solr/newseye_collection/select?fl=label_{language}_ssi&fq=id:{entity}&q=*:*"  # noqa: E501
            log.error(f"SOLR QUERY: {solr_query}")
            reply = requests.get(solr_query).json()
            log.error(f"SOLR RESPONSE: {reply}")
            name = reply["response"]["docs"][0][f"label_{language}_ssi"]
            log.error(f"SOLR NAME: {name}")
            return name
        except Exception as ex:
            log.error(f"SOLR ERROR: {ex}")
            return None

    def parse_messages(self, task_result: TaskResult, context: List[TaskResult], language: str) -> List[Message]:

        language = language.split("-")[0]

        if not task_result.processor == "TrackNameSentiment":
            raise WrongResourceException()

        corpus, corpus_type = self.build_corpus_fields(task_result)

        entries: Dict[str, Dict[int, Tuple[float, float]]] = {}
        for entity in task_result.task_result["result"]:
            entity_name_map: Dict[str, str] = task_result.task_result["result"][entity].get("names")
            if entity_name_map is None:
                entity_name_map = {}
            entity_name_priority_list = [
                entity_name_map.get(language, None),
                entity_name_map.get("en", None),
                list(entity_name_map.values())[0] if list(entity_name_map.values()) else None,
                entity,
            ]

            if not entity_name_map:
                entity_name_priority_list.insert(0, self._resolve_name_from_solr(entity, language))

            name = next(name for name in entity_name_priority_list if name)

            years: Dict[int, Tuple[float, float]] = {}
            for year in task_result.task_result["result"][entity]:
                if year == "names":
                    # Skip the names-map
                    continue
                sentiment = task_result.task_result["result"][entity][year]
                interestingness = task_result.task_result["interestingness"][entity][1][year]
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
                        "TrackNameSentiment:Mean",
                        "[ENTITY:NAME:{}]".format(entry),
                        mean_sentiment,
                        max_interestingness,
                        "[LINK:{}]".format(task_result.uuid),  # uuid
                    )
                )
            )

            if len(years) > 1:
                messages.append(
                    Message(
                        Fact(
                            corpus,
                            corpus_type,
                            min_year,
                            max_year,
                            "between_years",
                            "TrackNameSentiment:CountYears",
                            "[ENTITY:NAME:{}]".format(entry),
                            year_count,
                            max_interestingness,
                            "[LINK:{}]".format(task_result.uuid),  # uuid
                        )
                    )
                )
                messages.append(
                    Message(
                        Fact(
                            corpus,
                            corpus_type,
                            min_sentiment_year,
                            min_sentiment_year,
                            "year",
                            "TrackNameSentiment:Min",
                            "[ENTITY:NAME:{}]".format(entry),
                            min_sentiment,
                            max_interestingness,
                            "[LINK:{}]".format(task_result.uuid),  # uuid
                        )
                    ),
                )
                messages.append(
                    Message(
                        Fact(
                            corpus,
                            corpus_type,
                            max_sentiment_year,
                            max_sentiment_year,
                            "year",
                            "TrackNameSentiment:Max",
                            "[ENTITY:NAME:{}]".format(entry),
                            max_sentiment,
                            max_interestingness,
                            "[LINK:{}]".format(task_result.uuid),  # uuid
                        )
                    )
                )

        return messages

    def slot_realizer_components(self) -> List[Type[SlotRealizerComponent]]:
        return []
