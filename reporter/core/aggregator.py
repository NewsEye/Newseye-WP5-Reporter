from .pipeline import NLGPipelineComponent
from .template import Template, Literal, Slot
from .templates.substitutions import FactFieldSource
from .message import Message
from .document_plan import Relation

import re

import logging
log = logging.getLogger('root')


class Aggregator(NLGPipelineComponent):
    value_type_re = re.compile(
        r'([0-9_a-z]+?)(_normalized)?(?:(_mk_score|_mk_trend)|(_percentage)?(_change)?(?:(?:_grouped_by)(_time_place|_crime_time|_crime_place_year))?((?:_decrease|_increase)?_rank(?:_reverse)?)?)')

    def run(self, registry, random, language, document_plan):
        if log.isEnabledFor(logging.DEBUG):
            document_plan.print_tree()

        log.debug("Aggregating")
        self._aggregate(registry, language, document_plan)

        if log.isEnabledFor(logging.DEBUG):
            document_plan.print_tree()

        return document_plan

    def _aggregate_sequence(self, registry, language, this):
        log.debug("Visiting {}".format(this))

        num_children = len(this.children)
        new_children = []
        for idx in range(0, num_children):
            if idx > 0:
                t0 = new_children[-1]
            else:
                t0 = None
            t1 = self._aggregate(registry, language, this.children[idx])

            log.debug("t0={}, t1={}".format(t0, t1))

            if self._same_prefix(t0, t1) and not (t0.prevent_aggregation or t1.prevent_aggregation):
                log.debug("Combining")
                new_children[-1] = self._combine(registry, language, new_children[-1], t1)
                log.debug("Combined, New Children: {}".format(new_children))

            else:
                new_children.append(t1)
                log.debug("Did not combine. New Children: {}".format(new_children))

        this.children.clear()
        this.children.extend(new_children)
        return this

    def _aggregate_elaboration(self, registry, language, this):
        log.debug("Visiting {}".format(this))

        num_children = len(this.children)
        new_children = [this.children[0]]
        for idx in range(1, num_children):
            t0 = this.children[idx - 1]
            t1 = this.children[idx]

            log.debug("t0={}, t1={}".format(t0, t1))

            new_children[-1] = self._elaborate(registry, language, t0, t1)
            log.debug("Combined, New Children: {}".format(new_children))

        if len(new_children) == 1:
            return new_children[0]
        this.children.clear()
        this.children.extend(new_children)
        return this

    def _aggregate_list(self, registry, language, this):
        log.debug("Visiting {}".format(this))
        first_msg = this.children[0]
        template = first_msg.template
        for idx, slot in enumerate(template.components):
            if slot.slot_type == 'what':
                what_idx = idx
            elif slot.slot_type == 'what_type':
                what_type_idx = idx
        if what_idx < what_type_idx:
            start_idx = what_idx
            end_idx = what_type_idx + 1
        else:
            start_idx = what_type_idx
            end_idx = what_idx + 1
        start_slots = template.components[:start_idx]
        end_slots = template.components[end_idx:]
        combined_facts = []
        inner_components = []
        for idx, msg in enumerate(this.children):
            inner_slots = [slot.copy() for slot in template.components[start_idx:end_idx]]
            for slot in inner_slots:
                slot.fact = msg.fact
                if idx > 0 and slot.slot_type == 'what_type':
                    slot.attributes['no_normalization'] = True
                if idx < len(this.children) - 1 and slot.slot_type == 'what_type':
                    slot.attributes['no_grouping'] = True
            inner_components.append(inner_slots)
            combined_facts.append(msg.fact)
        combined_slots = start_slots
        for i in range(len(inner_components) - 2):
            combined_slots.extend(inner_components[i])
            combined_slots.append(Literal(","))
        if len(inner_components) > 1:
            combined_slots.extend(inner_components[-2])
            combined_slots.append(Literal(registry.get('vocabulary').get(language, {}).get('default_combiner', "MISSING-COMBINER")))
        combined_slots.extend(inner_components[-1])
        combined_slots.extend(end_slots)
        new_message = Message(facts=combined_facts, importance_coefficient=first_msg.importance_coefficient)
        new_message.template = Template(combined_slots)
        new_message.prevent_aggregation = True
        return new_message

    def _same_prefix(self, first, second):
        try:
            return first.components[0].value == second.components[0].value
        except AttributeError:
            return False

    def _combine(self, registry, language, first, second):
        log.debug("Combining {} and {}".format([c.value for c in first.components], [c.value for c in second.components]))
        combined = [c for c in first.components]
        for idx, other_component in enumerate(second.components):
            if idx >= len(combined):
                break
            this_component = combined[idx]
            if not self._are_same(this_component, other_component):
                break
        log.debug("idx = {}".format(idx))
        # ToDo! At the moment everything is considered either positive or negative, which is sometimes weird. Add neutral sentences.
        if self._message_positive(first) != self._message_positive(second):
            combined.append(Literal(registry.get('vocabulary').get(language, {}).get('inverse_combiner', "MISSING-COMBINER")))
        else:
            combined.append(Literal(registry.get('vocabulary').get(language, {}).get('default_combiner', "MISSING-COMBINER")))
        combined.extend(second.components[idx:])
        log.debug("Combined thing is {}".format([c.value for c in combined]))
        new_message = Message(facts=first.facts + [fact for fact in second.facts if fact not in first.facts], importance_coefficient=first.importance_coefficient)
        new_message.template = Template(combined)
        new_message.prevent_aggregation = True
        return new_message

    def _elaborate(self, registry, language, first, second):
        log.debug("Elaborating {} with {}".format([c.value for c in first.components], [c.value for c in second.components]))
        result = [c for c in first.components]
        try:
            first_type = first.facts[0].what_type
            second_type = second.facts[0].what_type

            # TODO: Refactor this away
            match_1 = self.value_type_re.fullmatch(first_type)
            match_2 = self.value_type_re.fullmatch(second_type)
            unit_1, normalized_1, trend_1, percentage_1, change_1, grouped_by_1, rank_1 = match_1.groups()
            unit_2, normalized_2, trend_2, percentage_2, change_2, grouped_by_2, rank_2 = match_2.groups()

            if (unit_1, normalized_1, percentage_1) == (unit_2, normalized_2, percentage_2) and not change_1 and change_2:
                result.append(Literal(
                    registry.get('vocabulary').get(language, {}).get('subord_clause_start', "MISSING-COMBINER")))
                result.append(Slot(FactFieldSource('what'), fact=second.facts[0]))
                result.append(Slot(FactFieldSource('what_type'), fact=second.facts[0]))
                result[-1].attributes['form'] = 'full'
                result.append(Literal(registry.get('vocabulary').get(language, {}).get('comparator', "MISSING-COMBINER")))
                result.append(Slot(FactFieldSource('when_1'), fact=second.facts[0]))
            else:
                result.append(Literal("("))
                result.append(Slot(FactFieldSource('what'), fact=second.facts[0]))
                result.append(Slot(FactFieldSource("what_type"), fact=second.facts[0]))
                attributes = {"form": "short", "case": "partitive"}
                result[-1].attributes = attributes
                result.append(Literal(")"))
        except KeyError:
            return self._combine(registry, language, first, second)
        new_message = Message(facts=first.facts + [fact for fact in second.facts if fact not in first.facts], importance_coefficient=first.importance_coefficient)
        new_message.template = Template(result)
        new_message.prevent_aggregation = first.prevent_aggregation or second.prevent_aggregation
        return new_message

    def _are_same(self, c1, c2):
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

    def _aggregate(self, registry, language, this):
        log.debug("Visiting {}".format(this))

        # Check the relation attribute and call the appropriate aggregator.
        try:
            relation = this.relation
        # If the node doesn't have a relation attribute, it is a message and should be simply returned
        except AttributeError:
            return this

        if relation == Relation.ELABORATION:
            return self._aggregate_elaboration(registry, language, this)
        elif relation == Relation.LIST:
            return self._aggregate_list(registry, language, this)
        return self._aggregate_sequence(registry, language, this)

    def _message_positive(self, message):
        fact = message.template.slots[0].fact
        try:
            return fact.what <= 0 or '_decrease_rank' in fact.what_type
        # This will happen if the fact is non-numeric
        except TypeError:
            return True
