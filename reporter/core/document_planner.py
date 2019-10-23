import logging
from random import Random
from typing import List, Union, Tuple, cast

from .models import Fact, DocumentPlanNode, Message, Relation
from .pipeline import NLGPipelineComponent
from .registry import Registry
from .template_selector import TemplateMessageChecker

log = logging.getLogger("root")

# For now, these parameters are hard-coded
MIN_PARAGRAPHS_PER_DOC = 3  # Try really hard to get at least this many
MAX_PARAGRAPHS_PER_DOC = 100
SENTENCES_PER_PARAGRAPH = 7
# How many messages are we allowed to take from the expanded set
MAX_EXPANDED_NUCLEI = 2

END_PARAGRAPH_RELATIVE_TRESHOLD = 0.0000001
END_PARAGRAPH_ABSOLUTE_THRESHOLD = 0.0

END_STORY_RELATIVE_TRESHOLD = 0.0000001
END_STORY_ABSOLUTE_TRESHOLD = 0.0


class NoInterestingMessagesException(Exception):
    pass


class HeadlineDocumentPlanner(NLGPipelineComponent):
    def run(
        self, registry: Registry, random: Random, language: str, scored_messages
    ) -> Tuple[DocumentPlanNode, List[Message]]:
        """
        Run this pipeline component.
        """

        log.debug("Creating headline document plan")

        # Root contains a sequence of children
        dp = DocumentPlanNode(children=[], relation=Relation.SEQUENCE)

        headline_message = scored_messages[0]
        all_messages = scored_messages

        dp.children.append(
            DocumentPlanNode(children=[headline_message], relation=Relation.SEQUENCE)
        )

        return dp, all_messages


class BodyDocumentPlanner(NLGPipelineComponent):
    """
    NLGPipeline that creates a DocumentPlan from the given nuclei and satellites.
    """

    def run(
        self, registry: Registry, random: Random, language: str, scored_messages: List[Message]
    ) -> Tuple[DocumentPlanNode, List[Message]]:
        """
        Run this pipeline component.
        """

        log.debug("Creating body document plan")

        # Root contains a sequence of children
        dp = DocumentPlanNode(children=[], relation=Relation.SEQUENCE)

        nuclei = []
        all_messages = scored_messages

        # In the first paragraph, don't ever use a message that's been added during expansion
        # These are recognisable by having a <1 importance coefficient
        core_messages = [sm for sm in scored_messages if sm.importance_coefficient >= 1.0]
        if not core_messages:
            raise NoInterestingMessagesException

        # Prepare a template checker
        template_checker = TemplateMessageChecker(registry.get("templates")[language], all_messages)

        # The children of the root are sequences of messages, with the nuclei
        # as first elements.
        max_score = 0.0
        expanded_nuclei = 0

        for par_num in range(MAX_PARAGRAPHS_PER_DOC):
            if (par_num == 0 and len(core_messages)) or expanded_nuclei >= MAX_EXPANDED_NUCLEI:
                penalized_candidates = self._penalize_similarity(core_messages, nuclei)
            else:
                penalized_candidates = self._penalize_similarity(scored_messages, nuclei)

            if len(penalized_candidates) == 0:
                break

            for message in penalized_candidates:
                # TODO: Here there used to be logic forcing a location to be expressed. We need similar logic but more generic for the complete context (time, corpus, query, etc)
                if template_checker.exists_template_for_message(message):
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
                    log.info(
                        "Nucleus score dropped below 20% of max score so far, stopping adding paragraphs"
                    )
                    break
                if message.score < END_STORY_ABSOLUTE_TRESHOLD:
                    # This absolute score is simply very low, so we're probably scraping the bottom of the barrel
                    log.info(
                        "Nucleus score dropped to a low absolute value, stopping adding paragraphs"
                    )
                    break

            # Check whether the added nucleus was from the expanded set
            if message.importance_coefficient < 1.0:
                expanded_nuclei += 1

            message.prevent_aggregation = True
            nuclei.append(message)
            messages = [message]
            # Drop the chosen message from the lists of remaining messages
            scored_messages = [m for m in scored_messages if m is not message]
            core_messages = [m for m in core_messages if m is not message]

            # Select satellites
            par_length = 1
            satellite_candidates = self._encourage_similarity(scored_messages, message)
            for satellite in satellite_candidates:
                if (
                    satellite.score == 0
                    or satellite.score < END_PARAGRAPH_ABSOLUTE_THRESHOLD
                    or satellite.score < message.score * END_PARAGRAPH_RELATIVE_TRESHOLD
                ):
                    log.info("No more interesting things to include in paragraph, ending it")
                    break

                # TODO: Drop messages that have been EFFECTIVELY TOLD by another semantically-equivalent message

                # TODO: use END_STORY_RELATIVE_TRESHOLD to block this thing
                # Only use the fact if we have a template to express it
                # Otherwise skip to the next most relevant
                if template_checker.exists_template_for_message(satellite):

                    self._add_satellite(satellite, messages)

                    # Drop the chosen message from the lists of remaining messages
                    scored_messages = [m for m in scored_messages if m is not satellite]
                    core_messages = [m for m in core_messages if m is not satellite]

                    par_length += 1
                    if par_length >= SENTENCES_PER_PARAGRAPH:
                        log.info("Reached max length of paragraph, ending it")
                        break

                else:
                    log.warning(
                        "I wanted to express {}, but had no template for it".format(
                            satellite.main_fact
                        )
                    )

            dp.children.append(DocumentPlanNode(children=messages, relation=Relation.SEQUENCE))

            max_score = max(message.score, max_score)

        return dp, all_messages

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
                # TODO: "Expected type 'Iterable[Message]', got 'List[TemplateComponent]' instead"
                todo.extend([c for c in m.children if c])
        return flat

    def _penalize_similarity(
        self, candidates: List[Message], nuclei: List[Message]
    ) -> List[Message]:
        # TODO: This is domain specific, consider splitting this off to a domain-specific method in a subclass
        return candidates
        if not nuclei:
            return candidates
        for nucleus in nuclei:
            # TODO: This is pretty meaningless in the toy dataset we are using now
            candidates = [
                msg
                for msg in candidates
                if nucleus.main_fact.analysis_type != msg.main_fact.analysis_type
            ]
        return candidates

    def _encourage_similarity(self, candidates: List[Message], nucleus: Message) -> List[Message]:
        # TODO: This is domain specific, consider splitting this off to a domain-specific method in a subclass
        # TODO: This is pretty meaningless in the toy dataset we are using now
        return [
            msg
            for msg in candidates
            if nucleus.main_fact.analysis_type == msg.main_fact.analysis_type
        ]

    def _add_satellite(
        self, satellite: Message, messages: List[Union[DocumentPlanNode, Message]]
    ) -> None:
        for idx, msg in enumerate(messages):
            if not isinstance(msg, Message):
                # It's not a Message, so it must be a non-leaf DPN
                msg = cast(DocumentPlanNode, msg)

                # A DPN without any children is not a meaningful thing and should never happen
                assert len(msg.children) > 0

                # At this point all DPNs should be flat, so this is supposed to make sense
                assert isinstance(msg.children[-1], Message)
                last_child = cast(Message, msg.children[-1])

                if (
                    msg.relation == Relation.LIST
                    and last_child.main_fact.analysis_type == satellite.main_fact.analysis_type
                ):
                    msg.children.append(satellite)
                    return
                else:
                    continue

            # Check whether any ordering of the messages results in Elaboration or Exemplification
            for first, second in [(msg, satellite), (satellite, msg)]:
                rel = self._get_suitable_relation(first, second)
                if rel != Relation.SEQUENCE:
                    children = [first, second]
                    messages[idx] = DocumentPlanNode(children, rel)
                    return

            # Not elaboration/exemplification, check whether it's meaningful to use a Relation.LIST
            if self._is_same_stat_type(msg, satellite):
                children = [msg, satellite]
                messages[idx] = DocumentPlanNode(children, Relation.LIST)
                return

            # Nope, only Relation.SEQUENCE makes sense. We'll just leave it at that.

        messages.append(satellite)

    def _get_suitable_relation(self, msg_1: Message, msg_2: Message) -> Relation:
        fact_1 = msg_1.main_fact
        fact_2 = msg_2.main_fact

        if self._is_contrastion(fact_1, fact_2):
            return Relation.CONTRAST
        elif self._is_elaboration(fact_1, fact_2):
            return Relation.ELABORATION
        elif self._is_exemplification(fact_1, fact_2):
            return Relation.EXEMPLIFICATION
        return Relation.SEQUENCE

    def _is_contrastion(self, fact1: Fact, fact2: Fact) -> bool:
        # TODO: There used to be really complex logic here, it needs to be reintroduced
        return False

    def _is_elaboration(self, fact1: Fact, fact2: Fact) -> bool:
        # TODO: There used to be really complex logic here, it needs to be reintroduced
        return False

    def _is_exemplification(self, fact1: Fact, fact2: Fact) -> bool:
        # TODO: There used to be really complex logic here, it needs to be reintroduced
        return False

    def _is_same_stat_type(self, msg1: Fact, msg2: Fact) -> bool:
        # TODO: There used to be really complex logic here, it needs to be reintroduced
        return False
