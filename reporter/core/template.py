import logging
from typing import Callable, Union, Any, List, Optional, Dict, NoReturn

from reporter.core import Fact, Message
from .document_plan import DocumentPlan
from .templates.substitutions import LiteralSource

log = logging.getLogger('root')


class TemplateComponent(object):
    """An abstract TemplateComponent. Should not be used directly."""

    def __init__(self) -> None:
        self._parent = None

    @property
    def value(self) -> NoReturn:
        raise NotImplementedError

    @value.setter
    def value(self, value) -> NoReturn:
        raise NotImplementedError

    @property
    def parent(self) -> 'TemplateComponent':
        return self._parent

    @parent.setter
    def parent(self, parent: 'TemplateComponent') -> None:
        self._parent = parent

    def __str__(self) -> str:
        return '[AbstractTemplateComponent]'


class Slot(TemplateComponent):
    """
    A TemplateComponent that can be filled by a Fact that fulfills a set of
    requirements.
    """

    def __init__(self, to_value: Callable, attributes: Optional[Dict[Any]] = None, fact: Optional[Fact] = None) -> None:
        """
        :param to_value: A callable that defines how to transform the message
            that fills this slot into a textual representation.
        """

        super().__init__()
        self.attributes = attributes or {}
        self._to_value = to_value
        self._fact = fact
        self._slot_type = self._to_value.field_name

    @property
    def slot_type(self) -> str:
        return self._slot_type

    @property
    def fact(self) -> Fact:
        return self._fact

    @fact.setter
    def fact(self, new_fact: Fact) -> None:
        self._fact = new_fact

    @property
    def value(self) -> Union[str, int, float]:
        return self._to_value(self._fact)

    @value.setter
    def value(self, f: Callable) -> None:
        self._to_value = f

    def copy(self) -> 'Slot':
        return Slot(self._to_value, self.attributes.copy())

    def __str__(self) -> str:
        return "Slot({}{})".format(
            self.value,
            "".join(", {}={}".format(k, v) for (k, v) in self.attributes.items())
        )


class LiteralSlot(Slot):
    def __init__(self, value: str, to_value: Callable, attributes: Optional[Dict[str, str]] = None) -> None:
        super().__init__(LiteralSource(value), attributes or {})
        self._fact = None
        self._slot_type = "Literal"


class Literal(TemplateComponent):
    """A string literal."""

    def __init__(self, string: str) -> None:
        super().__init__()
        self._string = string

    @property
    def slot_type(self) -> str:
        return 'Literal'

    @property
    def value(self) -> str:
        return self._string

    def copy(self) -> 'Literal':
        return Literal(self.value)

    def __str__(self) -> str:
        return self.value


class Template(DocumentPlan):
    """
    A template consisting of TemplateComponent elements and a list of rules about the facts that can be presented
    using the template.
    """

    def __init__(self, components: List[TemplateComponent], rules: List[Any] = None,
                 slot_map: Optional[Dict[Any, Any]] = None) -> None:
        super().__init__()
        self._rules = rules if rules is not None else []
        self._rules = rules
        self._facts = []
        self._slot_map = slot_map
        if self._slot_map is None:
            self._slot_map = {}
        self._components = components
        for c in self._components:
            c.parent = self

        self._expresses_location = None
        self._slots = None

    def get_slot(self, slot_type: str) -> Slot:
        """
        First version of the slot_map: here we are making an assumption that there is only one instance per slot type,
        which is clearly not true after aggregation. Whether this will be a problem is still a bit unclear.

        :param slot_type:
        :return:
        """
        if slot_type not in self._slot_map.keys():
            for slot in self.slots:
                if slot.slot_type == slot_type:
                    self._slot_map[slot_type] = slot
                    break
            else:
                self._slot_map[slot_type] = None
        if self._slot_map[slot_type] is None:
            raise KeyError
        return self._slot_map[slot_type]

    def add_slot(self, idx: int, slot: Slot) -> None:
        if len(self._components) > idx:
            self._components.insert(idx, slot)
        else:
            self._components.append(slot)
        slot.parent = self
        self.slots.append(slot)

    def move_slot(self, from_idx: int, to_idx: int) -> None:
        if from_idx >= to_idx:
            self.components.insert(to_idx, self.components.pop(from_idx))
        else:
            self.components.insert(to_idx - 1, self.components.pop(from_idx))

    @property
    def components(self) -> List[TemplateComponent]:
        return self._components

    @property
    def children(self) -> List[TemplateComponent]:
        return self._components

    @property
    def facts(self) -> List[Fact]:
        return self._facts

    def check(self, primary_message: Message, all_messages: List[Message], fill_slots: bool = False) -> List[Fact]:
        """
        Like fill(), but doesn't modify the template data structure, just checks whether the given message,
        with the support from other messages, is compatible with the template.

        :param primary_message: The message that the first rule in the template should match
        :param all_messages: A list of other available messages
        :param fill_slots:
        :return: True, if the template can be used for the primary_message. False otherwise.
        """
        # ToDo: Could we somehow cache the information about which messages to use in addition to the primary, so that we could then fill the message straight away without going through the messages again?
        # OR: Fill the templates in this phase and then just choose one of them. Filling shouldn't be that much slower than checking.
        primary_fact = primary_message.fact

        used_facts = []

        # The first rule has to match the primary message
        if not all(matcher(primary_fact, used_facts) for matcher in self._rules[0][0]):
            return []
        if fill_slots:
            for slot_index in self._rules[0][1]:
                self._components[slot_index].fact = primary_fact
        used_facts.append(primary_fact)
        # Check the other rules
        if len(self._rules) > 1:
            for (matchers, slot_indexes) in self._rules[1:]:
                # Try each message in turn
                for mess in all_messages:
                    if all(matcher(mess.fact, used_facts) for matcher in matchers):
                        # Found a suitable message: fill the slots
                        if fill_slots:
                            for slot_index in slot_indexes:
                                self._components[slot_index].fact = mess.fact
                        if mess.fact not in used_facts:
                            used_facts.append(mess.fact)
                        # Move onto the next rule
                        break
                else:
                    # No available message matched the rule: we can't use this template:
                    return []
        if fill_slots:
            self._facts = used_facts
        return used_facts

    def fill(self, primary_message: Message, all_messages: List[Message]) -> List[Fact]:
        """
        Search for messages needed to fulfill all of the rules in the template, and link the Slot components to the
        matching Facts

        :param primary_message: The message that the first rule in the template should match
        :param all_messages: A list of other available messages
        :return: A list of the Facts that match the rules in the template
        """

        return self.check(primary_message, all_messages, fill_slots=True)

    @property
    def slots(self) -> List[Slot]:
        # Cache the list of slots to avoid doing too many ifinstance checks
        # The slots are not guaranteed to be in the same order as they appear in the self._components
        if self._slots is None:
            self._slots = [c for c in self.components if isinstance(c, Slot)]
        return self._slots

    @property
    def expresses_location(self) -> bool:
        """ Whether this template expresses the location (where field) of any of its messages
        """
        if self._expresses_location is None:
            # Check each slot to see whether it expresses a where field
            for slot in self.slots:
                if slot.slot_type == "where":
                    self._expresses_location = True
                    break
            else:
                # No location field found: we assume the location is not expressed
                self._expresses_location = False
        return self._expresses_location

    def copy(self) -> 'Template':
        """Makes a deep copy of this Template. The copy does not contain any messages."""
        component_copy = [c.copy() for c in self.components]
        return Template(component_copy, self._rules)

    def __str__(self) -> str:
        return "<Template: n_components={}>".format(len(self.components))

    def display_template(self) -> str:
        """String representation of whole template, mainly for debugging"""
        return "".join(str(c) for c in self.components)


class DefaultTemplate(Template):

    def __init__(self, canned_text: str) -> None:
        super().__init__(components=[Literal(canned_text)])
