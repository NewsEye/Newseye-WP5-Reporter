from reporter.core import NLGPipelineComponent
from reporter.english_realizer import EnglishRealizer

import logging
import re
log = logging.getLogger('root')


class SlotRealizer(NLGPipelineComponent):

    def __init__(self):
        self._realizers = {
            'en': EnglishRealizer(),
        }
        self._realizer = None
        self._default_numeral = lambda x: "{:n}".format(x)
        self._default_unit = lambda x: None
        self._default_time = lambda x: None
        self._random = None

    def run(self, registry, random, language, document_plan):
        """
        Run this pipeline component.
        """
        log.info("Realizing slots")
        self._realizer = self._realizers[language[:2]]
        self._random = random
        self._recurse(document_plan)
        return document_plan,

    def _recurse(self, this):
        try:
            # Try to use the current root as a non-leaf.
            log.debug("Visiting non-leaf '{}'".format(this))
            # Use indexes to iterate through the children since the template slots may be edited, added or replaced
            # during iteration. Ugly, but will do for now.
            idx = 0
            while idx < len(this.children):
                slots_added = self._recurse(this.children[idx])
                if slots_added:
                    idx += slots_added
                idx += 1
        except AttributeError:
            # Had no children, must be a leaf node
            log.debug("Visiting leaf {}".format(this))
            try:
                slot_type = this.slot_type
            except AttributeError:
                log.info("Got an AttributeError when checking slot_type in realize_slots. Probably not a slot.")
                slot_type = 'n/a'
            if slot_type == 'what':
                added_slots = self._realize_value(this)
                return added_slots
            # Note that {time} slots aren't handled until at the NER, because they won't be realized every time.
            elif slot_type[:-2] == 'when':
                added_slots = self._realize_time(this)
                return added_slots
            elif slot_type == 'what_type':
                added_slots = self._realize_unit(this)
                return added_slots
            else:
                return 0

    def _realize_value(self, slot):
        try:
            what_type = slot.fact.what_type
            if 'rank' in what_type:
                slot.attributes['num_type'] = 'ordinal'
                num_type = 'ordinal'
            else:
                slot.attributes['num_type'] = 'cardinal'
                num_type = 'cardinal'
            value = slot.value
            if type(value) is str:
                return 0
            modified_value = self._realizer.numerals.get(num_type, self._default_numeral)(abs(value))
            slot.value = lambda x: modified_value
        except AttributeError:
            log.error("Error in value realization of slot {}".format(slot))
        return 0

    def _realize_unit(self, slot):
        value_type_re = re.compile(
            r'([0-9_a-z]+?)(_normalized)?(?:(_mk_score|_mk_trend)|(_percentage)?(_change)?(?:(?:_grouped_by)(_time_place|_crime_time|_crime_place_year))?((?:_decrease|_increase)?_rank(?:_reverse)?)?)')
        match = value_type_re.fullmatch(slot.value)
        unit, normalized, trend, percentage, change, grouped_by, rank = match.groups()
        try:
            if trend:
                new_slots = self._realizer.units.get('trend', self._default_unit)(slot)
            elif change:
                new_slots = self._realizer.units.get('change', self._default_unit)(slot)
            elif rank:
                new_slots = self._realizer.units.get('rank', self._default_unit)(slot)
            elif percentage:
                new_slots = self._realizer.units.get('percentage', self._default_unit)(slot)
            else:
                new_slots = self._realizer.units.get('base', self._default_unit)(slot)
            return new_slots
        except AttributeError:
            log.error("Error in unit realization of slot {}".format(slot))
            return 0

    def _realize_time(self, slot):
        try:
            return self._realizer.time.get(slot.fact.when_type, self._default_time)(self._random, slot)
        except AttributeError:
            log.error("Error in time realization of slot {}".format(slot))
            return 0
