import logging
import re
from random import Random
from typing import List, cast, Tuple

from .pipeline import NLGPipelineComponent
from .registry import Registry
from .document import DocumentPlanNode, Message, Literal, Relation, Slot, Template, TemplateComponent
from .templates.substitutions import FactFieldSource

log = logging.getLogger('root')


class Aggregator(NLGPipelineComponent):

    def run(self, registry: Registry, random: Random, language: str, document_plan: DocumentPlanNode) -> Tuple[DocumentPlanNode]:
        if log.isEnabledFor(logging.DEBUG):
            document_plan.print_tree()

        log.debug("Aggregating")
        self._aggregate(registry, language, document_plan)

        if log.isEnabledFor(logging.DEBUG):
            document_plan.print_tree()

        return (document_plan, )

    def _aggregate(self, registry: Registry, language: str, document_plan_node: DocumentPlanNode):  # Todo: Return type hint
        log.debug("Visiting {}".format(document_plan_node))

        # Cannot aggregate a single Message
        if isinstance(document_plan_node, Message):
            return document_plan_node

        if document_plan_node.relation == Relation.ELABORATION:
            return self._aggregate_elaboration(registry, language, document_plan_node)
        elif document_plan_node.relation == Relation.LIST:
            return self._aggregate_list(registry, language, document_plan_node)
        return self._aggregate_sequence(registry, language, document_plan_node)

    def _aggregate_sequence(self, registry: Registry, language: str, document_plan_node: DocumentPlanNode) -> DocumentPlanNode:
        log.debug("Visiting {}".format(document_plan_node))

        num_children = len(document_plan_node.children)
        new_children = []

        for idx in range(0, num_children):
            if idx > 0:
                previous_child = new_children[-1]
            else:
                previous_child = None
            current_child = self._aggregate(registry, language, document_plan_node.children[idx])

            log.debug("previous_child={}, current_child={}".format(previous_child, current_child))

            if self._same_prefix(previous_child, current_child) and not (previous_child.prevent_aggregation or current_child.prevent_aggregation):
                log.debug("Combining")
                new_children[-1] = self._combine(registry, language, new_children[-1], current_child)
                log.debug("Combined, New Children: {}".format(new_children))

            else:
                new_children.append(current_child)
                log.debug("Did not combine. New Children: {}".format(new_children))

        document_plan_node.children.clear()
        document_plan_node.children.extend(new_children)
        return document_plan_node

    def _aggregate_elaboration(self, registry: Registry, language: str, document_plan_node: DocumentPlanNode) -> DocumentPlanNode:
        # TODO: Re-implement this
        raise NotImplementedError

    def _aggregate_list(self, registry: Registry, language: str, document_plan_node: DocumentPlanNode) -> Message:
        # TODO: Re-implement this
        raise NotImplementedError

    def _same_prefix(self, first: Message, second: Message) -> bool:
        # TODO: Re-implement this
         return False

    def _combine(self, registry: Registry, language: str, first: Message, second: Message) -> Message:
        log.debug("Combining {} and {}".format([c.value for c in first.template.components], [c.value for c in second.template.components]))

        combined = [c for c in first.template.components]
        for idx, other_component in enumerate(second.template.components):
            if idx >= len(combined):
                break
            this_component = combined[idx]
            if not self._are_same(this_component, other_component):
                break
        log.debug("idx = {}".format(idx))
        # ToDo! At the moment everything is considered either positive or negative, which is sometimes weird. Add neutral sentences.
        if first.polarity != first.polarity:
            combined.append(
                Literal(registry.get('vocabulary').get(language, {}).get('inverse_combiner', "MISSING-COMBINER")))
        else:
            combined.append(
                Literal(registry.get('vocabulary').get(language, {}).get('default_combiner', "MISSING-COMBINER")))
        combined.extend(second.template.components[idx:])
        log.debug("Combined thing is {}".format([c.value for c in combined]))
        new_message = Message(facts=first.facts + [fact for fact in second.facts if fact not in first.facts],
                              importance_coefficient=first.importance_coefficient)
        new_message.template = Template(combined)
        new_message.prevent_aggregation = True
        return new_message

    def _are_same(self, c1: TemplateComponent, c2: TemplateComponent) -> bool:
        if c1.value != c2.value:
            # Are completely different, are not same
            return False

        try:
            if getattr(c1.fact, c1.slot_type + "_type") != getattr(c2.fact, c2.slot_type + "_type"):
                return False
        except AttributeError:
            pass

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
