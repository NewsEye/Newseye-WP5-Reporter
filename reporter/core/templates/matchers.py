import operator
import re
from typing import Any, List, Union

from reporter.core import Fact, Message


def equal_op(a: Union[object], b: Any) -> bool:
    if type(b) is str:
        return re.match('^' + b + '$', str(a)) is not None
    else:
        return operator.eq(a, b)


OPERATORS = {
    '=': equal_op,
    '!=': operator.ne,
    '>': operator.gt,
    '<': operator.lt,
    '>=': operator.ge,
    '<=': operator.le,
    'in': lambda a, b: operator.contains(b, a),
}


class LhsExpr(object):
    """Symbolic representation of expressions on the LHS of message constraints.

    We could just represent these expressions using lambda expressions, but this symbolic representation makes
    it easier to view them after they've been read in, to debug template reading, view templates, and so on.

    The __call__ methods perform the actual processing of the message to get a value to compare to the RHS
    of the constraint.
    """

    def __call__(self, fact: Fact, all_facts: List[Fact]) -> None:
        # Required in subclasses
        raise NotImplementedError()

    def __str__(self) -> str:
        # Required in subclasses
        raise NotImplementedError

    def __repr__(self) -> str:
        return str(self)


class FactField(LhsExpr):
    def __init__(self, field_name: str) -> None:
        self.field_name = field_name

    def __call__(self, fact: Fact, all_facts: List[Fact]) -> str:
        return getattr(fact, self.field_name)

    def __str__(self) -> str:
        return 'fact.{}'.format(self.field_name)


# TODO: Typing
class ReferentialExpr(object):
    def __init__(self, reference_idx: int, field_name: str) -> None:
        self.field_name = field_name
        self.reference_idx = reference_idx

    def __call__(self, message: Message, all_references: List[object]) -> str:
        return getattr(all_references[self.reference_idx], self.field_name)

    def __str__(self) -> str:
        return 'all[{}].{}'.format(self.reference_idx, self.field_name)


class Matcher(object):
    def __init__(self, lhs: LhsExpr, op: str, value: Any) -> None:
        if op not in OPERATORS:
            raise ValueError("invalid matcher operator '{}'. Must be one of: {}".format(op, ", ".join(OPERATORS)))
        self.value = value
        self.op = op
        self.lhs = lhs

    def __call__(self, fact: Fact, all_facts: List[Fact]):
        # Process the LHS expression
        result = self.lhs(fact, all_facts)
        if callable(self.value):
            value = self.value(fact, all_facts)
        else:
            value = self.value
        # Perform the relevant comparison operator
        return OPERATORS[self.op](result, value)

    def __str__(self):
        return "lambda msg, all: {} {} {}".format(self.lhs, self.op, self.value)

    def __repr__(self):
        return str(self)
