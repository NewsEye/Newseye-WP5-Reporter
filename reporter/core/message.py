from collections import namedtuple


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

    def __init__(self, facts, importance_coefficient=1.0, score=0.0, polarity=0.0):
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
    def facts(self):
        return self._facts

    @facts.setter
    def facts(self, new_facts):
        self._facts = new_facts

    @property
    def prevent_aggregation(self):
        return self._prevent_aggregation

    @prevent_aggregation.setter
    def prevent_aggregation(self, new_value):
        self._prevent_aggregation = new_value

    # Added for backwards compatibility, returns by default the primary fact for this Message.
    @property
    def fact(self):
        return self._main_fact

    @fact.setter
    def fact(self, new_fact):
        self._main_fact = new_fact

    # This is kind of ugly, and should be gotten rid of later, for now it's needed for some of the recursions to
    # work properly
    @property
    def children(self):
        return [self._template]

    @property
    def template(self):
        return self._template

    @template.setter
    def template(self, new_template):
        self._template = new_template

    @property
    def components(self):
        if self.template is None:
            return []
        else:
            return self.template.components

    @property
    def importance_coefficient(self):
        return self._importance_coefficient

    @importance_coefficient.setter
    def importance_coefficient(self, coeff):
        self._importance_coefficient = coeff

    @property
    def score(self):
        return self._score

    @score.setter
    def score(self, value):
        self._score = value

    @property
    def polarity(self):
        return self._polarity

    @polarity.setter
    def polarity(self, value):
        self._polarity = value

    def __str__(self):
        return "<Message>"
