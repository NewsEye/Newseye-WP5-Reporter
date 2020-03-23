import logging
from typing import List, Optional, Tuple

from reporter.core.document_planner import BodyDocumentPlanner, HeadlineDocumentPlanner
from reporter.core.models import Message

log = logging.getLogger("root")

MAX_PARAGRAPHS = 5

MAX_SATELLITES_PER_NUCLEUS = 10
MIN_SATELLITES_PER_NUCLEUS = 4

NEW_PARAGRAPH_ABSOLUTE_THRESHOLD = 0.5

SATELLITE_RELATIVE_THRESHOLD = 0.5
SATELLITE_ABSOLUTE_THRESHOLD = 0.2


class NewspaperBodyDocumentPlanner(BodyDocumentPlanner):
    def __init__(self) -> None:
        super().__init__(new_paragraph_absolute_threshold=NEW_PARAGRAPH_ABSOLUTE_THRESHOLD)

    def select_next_nucleus(
        self, available_message: List[Message], selected_nuclei: List[Message]
    ) -> Tuple[Message, float]:
        return _select_next_nucleus(available_message, selected_nuclei)

    def new_paragraph_relative_threshold(self, selected_nuclei: List[Message]) -> float:
        return _new_paragraph_relative_threshold(selected_nuclei)

    def select_satellites_for_nucleus(self, nucleus: Message, available_messages: List[Message]) -> List[Message]:
        return _select_satellites_for_nucleus(nucleus, available_messages)


class NewspaperHeadlineDocumentPlanner(HeadlineDocumentPlanner):
    def select_next_nucleus(
        self, available_message: List[Message], selected_nuclei: List[Message]
    ) -> Tuple[Message, float]:
        return _select_next_nucleus(available_message, selected_nuclei)


def _select_next_nucleus(
    available_messages: List[Message], selected_nuclei: List[Message]
) -> Tuple[Optional[Message], float]:

    log.debug("Starting a new paragraph")

    if len(selected_nuclei) >= MAX_PARAGRAPHS:
        log.debug("MAX_PARAGPAPHS reached, stopping")
        return None, 0

    selected_analyses = [nucleus.main_fact.analysis_type.split(":")[0] for nucleus in selected_nuclei]
    log.debug("Already talked about {}".format(selected_analyses))

    available = [
        message
        for message in available_messages
        if message.main_fact.analysis_type.split(":")[0] not in selected_analyses
    ]

    if available:
        # There are still analysis results we have not discussed, we'll select from among those only by leaving
        # `available` as-is.
        log.debug(
            "{}/{} messages talk about a different analysis, considering those for nucleus".format(
                len(available), len(available_messages)
            )
        )
        pass
    elif not available and len(selected_analyses) > 1:
        # There are no unselected analyses, but we have already mentioned more than one. This means that this is an
        # overview-type document and we are done.
        log.debug("At least two analysis types already covered, no more available, stopping early")
        return None, 0
    elif not available and len(selected_analyses) == 1:
        # To get here, selected_analysis must be 1 (<= 0 makes no sense)
        # We have only ever seen one analysis type. This means that we're building a document of the indepth-type,
        # meaning that we should relax our criteria for thematic difference between the nuclei.
        log.debug("No new analysis types to cover, but only one covered so far. Relaxing criteria.")
        available = available_messages

    if not available:
        # TODO: This seems to occur at least in some edge cases. Needs to be determined whether it's supposed to or not.
        return None, 0

    available.sort(key=lambda message: message.score, reverse=True)
    next_nucleus = available[0]
    log.debug(
        "Most interesting thing is {} (int={}), selecting it as a nucleus".format(next_nucleus, next_nucleus.score)
    )

    return next_nucleus, next_nucleus.score


def _new_paragraph_relative_threshold(selected_nuclei: List[Message]) -> float:
    # Gotta have something, so we'll add the first nucleus not matter what
    if not selected_nuclei:
        return float("-inf")

    # We'd really like to get a second paragraph, so we relax the requirements a bit here
    if len(selected_nuclei) == 1:
        return 0.1 * selected_nuclei[0].score

    # We already have at least 2 paragraphs, so we can be picky about whether we continue or not
    return 0.3 * selected_nuclei[0].score


def _select_satellites_for_nucleus(nucleus: Message, available_messages: List[Message]) -> List[Message]:
    log.debug("Selecting satellites for {} from among {} options".format(nucleus, len(available_messages)))
    satellites: List[Message] = []
    available_messages = available_messages[:]  # Copy, s.t. we can modify in place

    previous = nucleus
    while True:

        # Modify scores to account for context
        scored_available = [(message.score, message) for message in available_messages if message.score > 0]
        scored_available = _weigh_by_analysis_similarity(scored_available, previous)
        scored_available = _weigh_by_analysis_similarity(scored_available, nucleus)
        scored_available = _weigh_by_context_similarity(scored_available, previous)

        # Filter out based on thresholds
        filtered_scored_available = [
            (score, message)
            for (score, message) in scored_available
            if score > SATELLITE_RELATIVE_THRESHOLD * nucleus.score or score > SATELLITE_ABSOLUTE_THRESHOLD
        ]
        log.debug("After rescoring for context, {} available satellites remain".format(len(scored_available)))

        if not filtered_scored_available:
            if len(satellites) >= MIN_SATELLITES_PER_NUCLEUS:
                log.debug("Done with satellites: MIN_SATELLITES_PER_NUCLEUS reached, no satellites pass filter.")
                return satellites
            elif scored_available:
                log.debug(
                    "No satellite candidates pass threshold but have not reached MIN_SATELLITES_PER_NUCLEUS. "
                    "Trying without filter."
                )
                filtered_scored_available = scored_available
            else:
                log.debug("Did not reach MIN_SATELLITES_PER_NUCLEUS, but ran out of candidates. Ending paragraphs.")
                return satellites

        if len(satellites) >= MAX_SATELLITES_PER_NUCLEUS:
            log.debug("Stopping due to having reaches MAX_SATELLITE_PER_NUCLEUS")
            return satellites

        filtered_scored_available.sort(key=lambda pair: pair[0], reverse=True)

        score, selected_satellite = filtered_scored_available[0]
        satellites.append(selected_satellite)
        log.debug("Added satellite {} (temp_score={})".format(selected_satellite, score))

        previous = selected_satellite
        available_messages = [message for message in available_messages if message != selected_satellite]


def _weigh_by_analysis_similarity(
    messages: List[Tuple[float, Message]], previous: Message
) -> List[Tuple[float, Message]]:

    weighted: List[Tuple[float, Message]] = []
    unprocessed: List[Message] = []

    # Given that the previous message has analysis_type of "a:b:c:d", we start trying prefixes longest-first,
    # i.e. starting with "a:b:c:d", then "a:b:c", then "a:b" etc.
    # Each message's score is then weighted by 1/n where n is how many'th prefix this is. That is,
    # "a:b:c:d" -> n=1, "a:b:c" -> n=2 etc.
    prev_analysis_type_fragments = previous.main_fact.analysis_type.split(":")
    for n, fragment_count in enumerate(reversed(range(len(prev_analysis_type_fragments)))):
        analysis_prefix = ":".join(prev_analysis_type_fragments[: fragment_count + 1])

        for score, message in messages:
            if message.main_fact.analysis_type.startswith(analysis_prefix):
                weighted.append((score * 1 / (n + 1), message))
            else:
                unprocessed.append((score, message))

        messages, unprocessed = unprocessed, []

    # Still need to process the messages which shared no prefix at all.
    weighted.extend((0, message) for (score, message) in unprocessed)
    return weighted


def _weigh_by_context_similarity(
    messages: List[Tuple[float, Message]], previous: Message
) -> List[Tuple[float, Message]]:
    weighted: List[Tuple[float, Message]] = []

    for score, message in messages:
        if previous.main_fact.corpus == message.main_fact.corpus:
            score *= 1.5

        if previous.main_fact.timestamp_from == message.main_fact.timestamp_from:
            score *= 1.1
        if previous.main_fact.timestamp_to == message.main_fact.timestamp_to:
            score *= 1.1

        if previous.main_fact.result_key == message.main_fact.result_key:
            score *= 5

        weighted.append((score, message))
    return weighted
