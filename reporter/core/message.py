from collections import namedtuple
from typing import List, Union

from reporter.core import Template, TemplateComponent

Fact = namedtuple('fact', [
    'where',
    'where_type',
    'what',
    'what_type',
    'when_1',
    'when_2',
    'when_type',
    'outlierness',
])


class Message(object):
    """
    Contains a list of Fact tuples, a template for presenting the facts, and various values that are computed based on
    the facts.

    _importance_coefficient: scales the importance of the message, allowing less relevant messages to be included in the
    article only if their importance is high enough to outweigh having a lower coefficient
    _polarity: tells whether the message is considered positive, neutral or negative. For now the value is -1, 0, or 1.
    _score: is the newsworthiness score, that is used to decide which messages to include in the news article
    _template: is a Template object that contains information on how to display the message

    """

    def __init__(self, facts: Union[List[Fact], Fact], importance_coefficient: float = 1.0, score: float = 0.0,
                 polarity: float = 0.0) -> None:
        if isinstance(facts, list):
            self._facts = facts
        else:
            self._facts = [facts]
        self._template = None
        self._importance_coefficient = importance_coefficient
        self._score = score
        self._polarity = polarity
        self._main_fact = self._facts[0]
        self._prevent_aggregation = False

    @property
    def facts(self) -> List[Fact]:
        return self._facts

    @facts.setter
    def facts(self, new_facts: Union[List[Fact], Fact]) -> None:
        if isinstance(new_facts, list):
            self._facts = new_facts
        else:
            self._facts = [new_facts]

    @property
    def prevent_aggregation(self) -> float:
        return self._prevent_aggregation

    @prevent_aggregation.setter
    def prevent_aggregation(self, new_value: bool) -> None:
        self._prevent_aggregation = new_value

    # Added for backwards compatibility, returns by default the primary fact for this Message.
    @property
    def fact(self) -> Fact:
        return self._main_fact

    @fact.setter
    def fact(self, new_fact: Fact) -> None:
        self._main_fact = new_fact

    # This is kind of ugly, and should be gotten rid of later, for now it's needed for some of the recursions to
    # work properly
    @property
    def children(self) -> List[Template]:
        return [self._template]

    @property
    def template(self) -> Template:
        return self._template

    @template.setter
    def template(self, new_template: Template) -> None:
        self._template = new_template

    @property
    def components(self) -> List[TemplateComponent]:
        if self.template is None:
            return []
        else:
            return self.template.components

    @property
    def importance_coefficient(self) -> float:
        return self._importance_coefficient

    @importance_coefficient.setter
    def importance_coefficient(self, coeff: float) -> None:
        self._importance_coefficient = coeff

    @property
    def score(self) -> float:
        return self._score

    @score.setter
    def score(self, value: float) -> None:
        self._score = value

    @property
    def polarity(self) -> float:
        return self._polarity

    @polarity.setter
    def polarity(self, value: float) -> None:
        self._polarity = value

    def __str__(self) -> str:
        return "<Message>"
