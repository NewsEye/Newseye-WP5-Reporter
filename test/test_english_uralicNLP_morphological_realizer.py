from unittest import TestCase, main

from reporter.core.models import Fact, FactField, FactFieldSource, LiteralSlot, Matcher, Message, Slot, Template
from reporter.english_uralicNLP_morphological_realizer import EnglishUralicNLPMorphologicalRealizer


class TestRealization(TestCase):
    def setUp(self):
        self.fact = Fact("1", "_", "_", "_", "_", "_", "_", "cat", "_")
        self.message = Message(self.fact)

        self.expr = FactField("corpus")
        self.matcher = Matcher(self.expr, "=", "1")
        self.rules = [([self.matcher], [0])]

        self.slot = Slot(FactFieldSource("result_value"))
        self.literal = LiteralSlot("literal")
        self.components = [self.slot, self.literal]

        self.template = Template(self.components, self.rules)
        self.template.fill(self.message, [self.message])

        self.realizer = EnglishUralicNLPMorphologicalRealizer()

    def test_no_attrs_slot_left_as_is(self):
        self.assertEqual("cat", self.realizer.realize(self.slot))

    def test_no_attrs_literal_left_as_is(self):
        self.assertEqual("literal", self.realizer.realize(self.literal))

    def test_gen_slot_realized_correctly(self):
        self.slot.attributes["case"] = "genitive"
        self.assertEqual("cat's", self.realizer.realize(self.slot))

    def test_gen_literal_realized_correctly(self):
        self.literal.attributes["case"] = "genitive"
        self.assertEqual("literal's", self.realizer.realize(self.literal))


if __name__ == "__main__":
    main()
