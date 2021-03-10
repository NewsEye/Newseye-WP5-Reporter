import logging
from collections import defaultdict
from typing import List, Tuple

from numpy.random import Generator

from reporter.core.models import DocumentPlanNode, Literal, Message, Slot, Template, TemplateComponent
from reporter.core.pipeline import NLGPipelineComponent
from reporter.core.registry import Registry

log = logging.getLogger("root")


class Aggregator(NLGPipelineComponent):
    def run(
        self, registry: Registry, random: Generator, language: str, document_plan: DocumentPlanNode
    ) -> Tuple[DocumentPlanNode]:
        if log.isEnabledFor(logging.DEBUG):
            document_plan.print_tree()

        log.debug("Aggregating")
        self._aggregate(registry, language, document_plan)

        if log.isEnabledFor(logging.DEBUG):
            document_plan.print_tree()

        return (document_plan,)

    def _aggregate(self, registry: Registry, language: str, document_plan_node: DocumentPlanNode) -> DocumentPlanNode:
        log.debug("Visiting {}".format(document_plan_node))

        # Cannot aggregate a single Message
        if isinstance(document_plan_node, Message):
            return document_plan_node
        return self._aggregate_sequence(registry, language, document_plan_node)

    def _aggregate_sequence(
        self, registry: Registry, language: str, document_plan_node: DocumentPlanNode
    ) -> DocumentPlanNode:
        log.debug("Visiting {}".format(document_plan_node))

        num_children = len(document_plan_node.children)
        new_children = []  # type: List[Message]

        for idx in range(0, num_children):
            if idx > 0:
                previous_child = new_children[-1]
            else:
                previous_child = None
            current_child = self._aggregate(registry, language, document_plan_node.children[idx])

            # TODO: current_child should be a Message but seems to be a DocumentPlanNode instead ¯\_(ツ)_/¯

            log.debug("previous_child={}, current_child={}".format(previous_child, current_child))

            if self._same_prefix(previous_child, current_child) and not (
                previous_child.prevent_aggregation or current_child.prevent_aggregation
            ):
                log.debug("Combining")
                new_children[-1] = self._combine(registry, language, new_children[-1], current_child)
                log.debug("Combined, New Children: {}".format(new_children))

            else:
                new_children.append(current_child)
                log.debug("Did not combine. New Children: {}".format(new_children))

        document_plan_node.children.clear()
        document_plan_node.children.extend(new_children)
        return document_plan_node

    def _get_combinable_prefix(self, first: Message, second: Message):
        try:
            getattr(first.template, "components")
            getattr(second.template, "components")
        except AttributeError:
            return []

        shared_prefix = []

        for m1_component, m2_component in zip(first.template.components, second.template.components):
            if self._are_same(m1_component, m2_component):
                shared_prefix.append(m1_component)
            else:
                break

        # This is a special case: "The search found 114385 articles in French." followed by
        # "The search found 114385 articles from the newspaper L oeuvre." should aggregate as
        # "The search found 14385 articles in French and 14385 articles from the newspaper L oeuvre"
        # despite there being no slots in the shared prefix. We identify this case by checking whether the component
        # following the prefix, in both templates, is a result_value slot.
        # We might be able to relax this to "any slot", but that requires a bunch more checking.
        # TODO: Check above.
        m1_following = first.template.components[len(shared_prefix)]
        m2_following = second.template.components[len(shared_prefix)]
        print(f"NEXT COMPONENTS: {m1_following} and {m2_following}")
        if isinstance(m1_following, Slot) and isinstance(m2_following, Slot):
            if m1_following.slot_type == "result_value" and m2_following.slot_type == "result_value":
                return shared_prefix

        # The standard case: the prefix must terminate in a slot. Due to self._are_same above, the prefix can't ever
        # contain a result_value slot, so no need to special case that.
        while shared_prefix and type(shared_prefix[-1]) != Slot:
            shared_prefix = shared_prefix[:-1]
        return shared_prefix

    def _same_prefix(self, first: Message, second: Message) -> bool:
        if first is None or second is None:
            return False
        return len(self._get_combinable_prefix(first, second)) > 0

    def _combine(self, registry: Registry, language: str, first: Message, second: Message) -> Message:
        log.debug(
            "Combining {} and {}".format(
                [c.value for c in first.template.components], [c.value for c in second.template.components]
            )
        )

        shared_prefix = self._get_combinable_prefix(first, second)
        log.debug(f"Shared prefix is {[e.value for e in shared_prefix]}")

        combined = [c for c in first.template.components]

        conjunctions = registry.get("CONJUNCTIONS").get(language, None)
        if not conjunctions:
            conjunctions = (defaultdict(lambda x: "NO-CONJUNCTION-DICT"),)
        combined.append(Literal(conjunctions.get("default_combiner", "MISSING-DEFAULT-CONJUCTION")))
        combined.extend(second.template.components[len(shared_prefix) :])
        log.debug("Combined thing is {}".format([c.value for c in combined]))
        new_message = Message(
            facts=first.facts + [fact for fact in second.facts if fact not in first.facts],
            importance_coefficient=first.importance_coefficient,
        )
        new_message.template = Template(combined)
        new_message.prevent_aggregation = True
        return new_message

    def _are_same(self, c1: TemplateComponent, c2: TemplateComponent) -> bool:
        if c1.value != c2.value:
            # Are completely different, are not same
            return False

        if isinstance(c1, Slot) and isinstance(c2, Slot):
            assert c1.fact is not None
            assert c2.fact is not None

            if (c1.slot_type == "time") != (c2.slot_type == "time"):
                return False
            elif c1.slot_type == "time" and c2.slot_type == "time":
                if not (
                    (c1.fact.timestamp_type == c2.fact.timestamp_type)
                    and (c1.fact.timestamp_from == c2.fact.timestamp_from)
                    and (c1.fact.timestamp_to == c2.fact.timestamp_to)
                ):
                    return False
            else:
                if getattr(c1.fact, c1.slot_type) != getattr(c2.fact, c2.slot_type):
                    return False

            # Aggregating numbers is a mess, and can easily lead to sentences like "The search found 114385 articles in
            # French and from the newspaper L oeuvre", which implies that there is a set of 114385 articles s.t. every
            # article in the set is both in french and published in L'ouvre. Unfortunately, it's possible to end up in
            # this situation even if the underlying data actually says that there were two sets of size 114385 s.t.
            # in one all are in french and in the other all were published in L'ouvre. That is, we do now in fact know
            # whether the sets contain the same documents or not.
            if c1.slot_type == "result_value":
                return False

        # They are apparently same, check cases
        c1_case = "no-case"
        c2_case = "no-case"
        try:
            c1_case = c1.attributes.get("case", "")
        except AttributeError:
            pass
        try:
            c2_case = c2.attributes.get("case", "")
        except AttributeError:
            pass

        # False if different cases or one had attributes and other didn't
        return c1_case == c2_case
