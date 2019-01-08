import logging
from random import Random
from typing import Tuple, List, Union, Iterable

from reporter.core import Registry
from .message import Message, Fact
from .pipeline import NLGPipelineComponent
from .document_plan import DocumentPlan, Relation
from .message_generator import NoMessagesForSelectionException
from .template_selector import TemplateMessageChecker
import re

log = logging.getLogger('root')

# For now, these parameters are hard-coded
MIN_PARAGRAPHS_PER_DOC = 3  # Try really hard to get at least this many
MAX_PARAGRAPHS_PER_DOC = 5
SENTENCES_PER_PARAGRAPH = 7
# How many messages are we allowed to take from the expanded set
MAX_EXPANDED_NUCLEI = 2

END_STORY_RELATIVE_TRESHOLD = 0.2
END_STORY_ABSOLUTE_TRESHOLD = 2.0


class HeadlineDocumentPlanner(NLGPipelineComponent):

    def run(self, registry: Registry, random: Random, language: str, scored_messages) \
            -> Tuple[DocumentPlan, List[Message]]:
        """
        Run this pipeline component.
        """

        log.debug("Creating headline document plan")

        # Root contains a sequence of children
        dp = DocumentPlan(children=[], relation=Relation.SEQUENCE)

        headline_message = scored_messages[0]
        all_messages = scored_messages

        dp.children.append(
            DocumentPlan(children=[headline_message], relation=Relation.SEQUENCE)
        )

        return dp, all_messages


class BodyDocumentPlanner(NLGPipelineComponent):
    """
    NLGPipeline that creates a DocumentPlan from the given nuclei and satellites.
    """

    # The capture groups are: (unit)(normalized)(percentage)(change)(grouped_by)(rank)
    value_type_re = re.compile(
        r'([0-9_a-z]+?)(_normalized)?(?:(_mk_score|_mk_trend)|(_percentage)?(_change)?(?:(?:_grouped_by)(_time_place|_crime_time|_crime_place_year))?((?:_decrease|_increase)?_rank(?:_reverse)?)?)')

    def run(self, registry: Registry, random: Random, language: str, scored_messages: List[Message]) -> Tuple[DocumentPlan, List[Message]]:
        """
        Run this pipeline component.
        """

        log.debug("Creating body document plan")

        # Root contains a sequence of children
        dp = DocumentPlan(children=[], relation=Relation.SEQUENCE)

        nuclei = []
        all_messages = scored_messages

        # Drop messages with rank or rank_reverse values of more than 4 and messages with comparisons between
        # municipalities using the reported values instead of normalized or percentage values
        scored_messages = [msg for msg in scored_messages
                           if not
                           # drop the message if it is about a rank or rank_reverse of more than 4 ...
                           (('_rank' in msg.fact.what_type and msg.fact.what > 4)
                            # ... or if the message is not normalized ...
                            or (
                                    not ('_normalized' in msg.fact.what_type
                                         # ... or percentage ...
                                         or '_percentage' in msg.fact.what_type)
                                    # ... and is comparing different municipalities
                                    and '_grouped_by_crime_time' in msg.fact.what_type)
                            # ... or the message is telling about one of the crimes that was done the least (aka zero times)
                            or ('_rank_reverse' in msg.fact.what_type and msg.fact.what == 1)
                            )]

        # In the first paragraph, don't ever use a message that's been added during expansion
        # These are recognisable by having a <1 importance coefficient
        core_messages = [sm for sm in scored_messages if sm.importance_coefficient >= 1.]
        if not core_messages:
            raise NoMessagesForSelectionException

        # Prepare a template checker
        template_checker = TemplateMessageChecker(registry.get("templates")[language], all_messages)

        # The children of the root are sequences of messages, with the nuclei
        # as first elements.
        max_score = 0.0
        expanded_nuclei = 0
        # Keep track of what location is currently being talked about
        current_location = None
        for par_num in range(MAX_PARAGRAPHS_PER_DOC):
            if (par_num == 0 and len(core_messages)) or expanded_nuclei >= MAX_EXPANDED_NUCLEI:
                penalized_candidates = self._penalize_similarity(core_messages, nuclei)
            else:
                penalized_candidates = self._penalize_similarity(scored_messages, nuclei)

            if len(penalized_candidates) == 0:
                break

            for message in penalized_candidates:
                require_location = current_location is None or message.fact.where != current_location
                # Check whether this nucleus is even expressable, given our templates and contextual requirements
                # (Currently no contextual requirements, but location expression will soon be constrained)
                # If the message can't be expressed, choose another one
                if template_checker.exists_template_for_message(message, location_required=require_location):
                    break
            else:
                # Couldn't express ANY of the messages! V. unlikely to happen
                # Use the first one and let later stages deal with the problems

                message = penalized_candidates[0]

            if message.score == 0:
                break

            # Once we've got the min pars per doc, we can apply stricter tests for whether it's worth continuing
            if par_num >= MIN_PARAGRAPHS_PER_DOC:
                if message.score < max_score * END_STORY_RELATIVE_TRESHOLD:
                    # We've dropped to vastly below the importance of the most important nucleus: time to stop nattering
                    log.info("Nucleus score dropped below 20% of max score so far, stopping adding paragraphs")
                    break
                if message.score < END_STORY_ABSOLUTE_TRESHOLD:
                    # This absolute score is simply very low, so we're probably scraping the bottom of the barrel
                    log.info("Nucleus score dropped to a low absolute value, stopping adding paragraphs")
                    break

            # Check whether the added nucleus was from the expanded set
            if message.importance_coefficient < 1.:
                expanded_nuclei += 1

            message.prevent_aggregation = True
            nuclei.append(message)
            messages = [message]
            current_location = message.fact.where
            # Drop the chosen message from the lists of remaining messages
            scored_messages = [m for m in scored_messages if m is not message]
            core_messages = [m for m in core_messages if m is not message]

            # Select satellites
            par_length = 1
            satellite_candidates = self._encourage_similarity(scored_messages, message)
            for satellite in satellite_candidates:
                if satellite.score == 0:
                    log.info("No more interesting things to include in paragraph, ending it")
                    break

                # Drop messages that have been EFFECTIVELY TOLD by another semantically-equivalent message
                if self._is_effectively_repetition(satellite, messages):
                    continue

                require_location = current_location is None or satellite.fact.where != current_location
                # Only use the fact if we have a template to express it
                # Otherwise skip to the next most relevant
                if template_checker.exists_template_for_message(satellite, location_required=require_location):

                    self._add_satellite(satellite, messages)
                    # Drop the chosen message from the lists of remaining messages
                    scored_messages = [m for m in scored_messages if m is not satellite]
                    core_messages = [m for m in core_messages if m is not satellite]
                    par_length += 1
                    if par_length >= SENTENCES_PER_PARAGRAPH:
                        log.info("Reached max length of paragraph, ending it")
                        break

                else:
                    log.warning('I wanted to express {}, but had no template for it'.format(satellite.fact))

            dp.children.append(
                DocumentPlan(children=messages, relation=Relation.SEQUENCE)
            )

            max_score = max(message.score, max_score)

        return dp, all_messages

    def _is_effectively_repetition(self, candidate: Message, messages: List[Message]) -> bool:
        unit, normalized, trend, percentage, change, grouped_by, rank = self.value_type_re.fullmatch(
            candidate.fact.what_type).groups()

        flat_messages = self._flatten(messages)
        if not flat_messages:
            return False

        for other in flat_messages:
            if candidate.fact.where != other.fact.where:
                # Not repetition if we are not even talking about the same location
                continue
            other_groups = self.value_type_re.fullmatch(other.fact.what_type).groups()
            (existing_unit, existing_normalized, existing_trend, existing_percentage, existing_change,
             existing_grouped_by, existing_rank) = other_groups
            if (unit == existing_unit
                    and percentage == existing_percentage
                    and change == existing_change
                    and grouped_by == existing_grouped_by
                    and (
                            (rank and existing_rank)
                            or (not rank and not existing_rank)
                    )):
                # Notably, we consider ranks and reverse ranks the same and similarly consider the normalized
                # variant of a fact to be repetitive with the un-normalized fact. 
                log.info("Skipping {}, as it's already being effectively told by {}".format(
                    candidate.fact.what_type,
                    other.fact.what_type
                ))
                return True
        log.debug("It does not seem to be repetition, including in DocumentPlan")
        return False

    def _flatten(self, messages: List[Message]) -> List[Message]:
        flat = []
        # Copy the list, since modifying it modifies also the resulting DocumentPlan.
        todo = messages[:]
        while todo:
            m = todo.pop()
            if isinstance(m, Message):
                flat.append(m)
            else:
                # Extend with non-None children
                todo.extend([c for c in m.children if c])
        return flat

    def _penalize_similarity(self, candidates: List[Message], nuclei: List[Message]) -> List[Message]:
        if not nuclei:
            return candidates
        # Pick only messages about crimes that belong to DIFFERENT generic crime type but share a location
        for nucleus in nuclei:
            candidates = [msg for msg in candidates
                          if (nucleus.fact.where == msg.fact.where
                              and nucleus.fact.what_type.split("_")[0] != msg.fact.what_type.split("_")[0])]
        return candidates

    def _encourage_similarity(self, candidates: List[Message], nucleus: Message) -> List[Message]:
        # Pick only messages about crimes that belong to the same generic crime type (in other words, that have a crime
        # type starting with the same prefix as the nucleus
        modified = [msg for msg in candidates
                    if (nucleus.fact.where == msg.fact.where
                        and nucleus.fact.what_type.split("_")[0] == msg.fact.what_type.split("_")[0]
                        and (
                                (msg.fact.when_2 == nucleus.fact.when_2)
                                or (msg.fact.when_1 == nucleus.fact.when_1 and msg.fact.when_2 == nucleus.fact.when_1)
                        )
                        )]
        return modified

    def _add_satellite(self, satellite: Message, messages: List[Union[DocumentPlan, Message]]) -> None:
        for idx, msg in enumerate(messages):
            if type(msg) is DocumentPlan:
                if msg.relation == Relation.LIST and self._is_same_stat_type(msg.children[-1], satellite):
                    msg.add_message(satellite)
                    return
                continue
            rel = self._check_relation(msg, satellite)
            if rel != Relation.SEQUENCE:
                children = [msg, satellite]
                messages[idx] = DocumentPlan(children, rel)
                return
            rel = self._check_relation(satellite, msg)
            if rel != Relation.SEQUENCE:
                children = [satellite, msg]
                messages[idx] = DocumentPlan(children, rel)
                return
            if self._is_same_stat_type(msg, satellite):
                children = [msg, satellite]
                messages[idx] = DocumentPlan(children, Relation.LIST)
                return
        messages.append(satellite)

    def _check_relation(self, msg_1: Message, msg_2: Message) -> Relation:
        """
        Returns the Relation type between msg_1 and msg_2
        :param msg_1:
        :param msg_2:
        :return:
        """
        fact_1 = msg_1.fact
        fact_2 = msg_2.fact

        # Comparison of the same what_type between different place or time
        if (fact_1.where != fact_2.where or fact_1.when_2 != fact_2.when_2) and \
                (fact_1.what_type == fact_2.what_type):
            return Relation.CONTRAST

        # msg_2 is an elaboration of msg_1
        elif self._is_elaboration(fact_1, fact_2):
            return Relation.ELABORATION
        elif self._is_exemplification(fact_1, fact_2):
            return Relation.EXEMPLIFICATION
        return Relation.SEQUENCE

    def _is_elaboration(self, fact1: Fact, fact2: Fact) -> bool:
        """

        :param fact1:
        :param fact2:
        :return: True, if fact2 is an elaboration of fact1, False otherwise
        """
        same_context = (fact1.where, fact1.when_1, fact1.when_2) == (fact2.where, fact2.when_1, fact2.when_2)
        if not same_context:
            return False
        # An elaboration can't have the same fact type in both facts.
        if fact1.what_type == fact2.what_type:
            return False
        match_1 = self.value_type_re.fullmatch(fact1.what_type)
        match_2 = self.value_type_re.fullmatch(fact2.what_type)
        unit_1, normalized_1, trend_1, percentage_1, change_1, grouped_by_1, rank_1 = match_1.groups()
        unit_2, normalized_2, trend_2, percentage_2, change_2, grouped_by_2, rank_2 = match_2.groups()
        # If the facts have different base unit, they can't have an elaboration relation
        if unit_1 != unit_2:
            return False
        # Rank values cannot be elaborations
        elif rank_2:
            return False
        # rank and rank_reverse are elaborated by the base values
        elif rank_1:
            return (change_1, None) == (change_2, grouped_by_2)
        # Change is an elaboration of the result value
        elif change_2 and (normalized_1, percentage_1) == (normalized_2, percentage_2):
            return True
        # total value is an elaboration of a percentage value
        elif change_1 is None and change_2 is None and percentage_1:
            return True
        else:
            return False

    def _is_exemplification(self, fact1: Fact, fact2: Fact) -> bool:
        """
        Should check, whether fact2 is an exemplification of fact1. This type doesn't exist at the moment, so
        will always return False
        :param fact1:
        :param fact2:
        :return:
        """
        return False

    def _is_same_stat_type(self, msg1: Fact, msg2: Fact) -> bool:
        match_1 = self.value_type_re.fullmatch(msg1.fact.what_type)
        match_2 = self.value_type_re.fullmatch(msg2.fact.what_type)
        # true if everything except the crime itself is the same and the what values have the same sign
        return match_1.groups()[1:] == match_2.groups()[1:] and msg1.fact.what * msg2.fact.what > 0
