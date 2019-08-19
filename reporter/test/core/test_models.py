from unittest import main, TestCase
from reporter.core.models import (
    Message,
    Fact,
    DocumentPlanNode,
    Document,
    Relation,
    TemplateComponent,
    Slot,
    LiteralSource,
    SlotSource,
    LiteralSlot,
    FactFieldSource,
    TimeSource,
    LhsExpr,
    FactField,
    ReferentialExpr,
    Matcher,
    Template,
)


class TestFact(TestCase):
    def setUp(self):
        self.fact = Fact(
            "corpus",
            "corpus_type",
            "timestamp_from",
            "timestamp_to",
            "timestamp_type",
            "analysis_type",
            "result_key",
            "result_value",
            "outlierness",
        )

    def test_fact_fields(self):
        self.assertEqual(self.fact.corpus, "corpus")
        self.assertEqual(self.fact.corpus_type, "corpus_type")
        self.assertEqual(self.fact.timestamp_from, "timestamp_from")
        self.assertEqual(self.fact.timestamp_to, "timestamp_to")
        self.assertEqual(self.fact.timestamp_type, "timestamp_type")
        self.assertEqual(self.fact.analysis_type, "analysis_type")
        self.assertEqual(self.fact.result_key, "result_key")
        self.assertEqual(self.fact.result_value, "result_value")
        self.assertEqual(self.fact.outlierness, "outlierness")


class TestMessage(TestCase):
    def setUp(self):
        self.fact1 = Fact(
            "corpus1",
            "corpus_type",
            "timestamp_from",
            "timestamp_to",
            "timestamp_type",
            "analysis_type",
            "result_key",
            "result_value",
            "outlierness",
        )
        self.fact2 = Fact(
            "corpus2",
            "corpus_type",
            "timestamp_from",
            "timestamp_to",
            "timestamp_type",
            "analysis_type",
            "result_key",
            "result_value",
            "outlierness",
        )

    def test_message_creation_single_fact(self):
        message = Message(self.fact1, 0.1, 0.2, 0.3)

        self.assertIsInstance(message.facts, list)
        self.assertNotIsInstance(message.facts, Fact)
        self.assertEqual(len(message.facts), 1)
        self.assertEqual(message.facts[0], self.fact1)
        self.assertEqual(message.main_fact, self.fact1)
        self.assertEqual(message.importance_coefficient, 0.1)
        self.assertEqual(message.score, 0.2)
        self.assertEqual(message.polarity, 0.3)
        self.assertIsNone(message.template)
        self.assertEqual(str(message), "<Message>")

    def test_message_creation_list_of_facts(self):
        message = Message([self.fact1, self.fact2], 0.1, 0.2, 0.3)

        self.assertIsInstance(message.facts, list)
        self.assertEqual(len(message.facts), 2)
        self.assertListEqual(message.facts, [self.fact1, self.fact2])
        self.assertEqual(message.main_fact, self.fact1)

    def test_message_set_facts_always_list1(self):
        message = Message(self.fact1, 0.1, 0.2, 0.3)
        message.facts = self.fact2

        self.assertIsInstance(message.facts, list)
        self.assertListEqual(message.facts, [self.fact2])
        self.assertEqual(message.main_fact, self.fact2)

    def test_message_set_facts_always_list2(self):
        message = Message(self.fact1, 0.1, 0.2, 0.3)
        message.facts = [self.fact2]

        self.assertIsInstance(message.facts, list)
        self.assertListEqual(message.facts, [self.fact2])
        self.assertEqual(message.main_fact, self.fact2)


class TestDocument(TestCase):
    def setUp(self):
        self.fact1 = Fact(
            "corpus1",
            "corpus_type",
            "timestamp_from",
            "timestamp_to",
            "timestamp_type",
            "analysis_type",
            "result_key",
            "result_value",
            "outlierness",
        )
        self.message1 = Message(self.fact1, 0.1, 0.2, 0.3)

        self.fact2 = Fact(
            "corpus2",
            "corpus_type",
            "timestamp_from",
            "timestamp_to",
            "timestamp_type",
            "analysis_type",
            "result_key",
            "result_value",
            "outlierness",
        )
        self.message2 = Message(self.fact2, 0.1, 0.2, 0.3)
        self.document_plan_node = DocumentPlanNode(
            [self.message1, self.message2], Relation.ELABORATION
        )
        self.document = Document("en", self.document_plan_node)

    def test_document_creation(self):
        self.assertEqual(self.document.language, "en")
        self.assertEqual(self.document.document_plan, self.document_plan_node)

    def test_document_messages_retrieves_all_messages(self):
        self.assertIn(self.message1, self.document.messages())
        self.assertIn(self.message2, self.document.messages())


class TestDocumentPlanNode(TestCase):
    def setUp(self):
        self.fact1 = Fact(
            "corpus1",
            "corpus_type",
            "timestamp_from",
            "timestamp_to",
            "timestamp_type",
            "analysis_type",
            "result_key",
            "result_value",
            "outlierness",
        )
        self.message1 = Message(self.fact1, 0.1, 0.2, 0.3)

        self.fact2 = Fact(
            "corpus2",
            "corpus_type",
            "timestamp_from",
            "timestamp_to",
            "timestamp_type",
            "analysis_type",
            "result_key",
            "result_value",
            "outlierness",
        )
        self.message2 = Message(self.fact2, 0.1, 0.2, 0.3)

        self.document_plan_node = DocumentPlanNode(
            [self.message1, self.message2], Relation.ELABORATION
        )

    def test_document_plan_node_creation_sets_values(self):
        self.assertListEqual(self.document_plan_node.children, [self.message1, self.message2])
        self.assertEqual(self.document_plan_node.relation, Relation.ELABORATION)
        self.assertEqual(str(self.document_plan_node), "ELABORATION")

    def test_document_plan_node_print_tree_does_not_crash(self):
        self.document_plan_node.print_tree()


class TestTemplateComponent(TestCase):
    def setUp(self):
        self.parent = TemplateComponent()
        self.component = TemplateComponent()

    def test_template_component_default_values(self):
        component = self.component

        self.assertIsNone(component.parent)
        self.assertEqual(str(component), "[AbstractTemplateComponent]")

    def test_template_sets_parent(self):
        self.component.parent = self.parent
        self.assertEqual(self.component.parent, self.parent)

    def test_is_abstract(self):
        with self.assertRaises(NotImplementedError):
            self.component.value()

        with self.assertRaises(NotImplementedError):
            self.component.value = "anything"

        with self.assertRaises(NotImplementedError):
            self.component.copy()


class TestSlot(TestCase):
    def setUp(self):
        self.to_value = LiteralSource("some literal")
        self.attributes = dict()
        self.fact = Fact(
            "corpus",
            "corpus_type",
            "timestamp_from",
            "timestamp_to",
            "timestamp_type",
            "analysis_type",
            "result_key",
            "result_value",
            "outlierness",
        )

    def test_slot_creation_with_default_values(self):
        slot = Slot(self.to_value)

        self.assertEqual(slot.value, "some literal")
        self.assertEqual(slot.slot_type, "literal")
        self.assertIsInstance(slot.attributes, dict)
        self.assertEqual(len(slot.attributes), 0)
        self.assertIsNone(slot.fact)

    def test_slot_creation_without_defaults(self):
        slot = Slot(self.to_value, self.attributes, self.fact)

        self.assertEqual(slot.attributes, self.attributes)
        self.assertEqual(slot.fact, self.fact)

    def test_slot_value_setter(self):
        slot = Slot(self.to_value)
        slot.value = LiteralSource("another literal")

        self.assertEqual(slot.value, "another literal")

    def test_slot_value_setter_updates_slot_type(self):
        slot = Slot(self.to_value)
        slot.value = SlotSource("a fake type")

        self.assertEqual(slot.slot_type, "a fake type")

    def test_slot_copy_copies_value_type_and_attributes(self):
        slot = Slot(self.to_value, self.attributes, self.fact)
        copy = slot.copy()

        self.assertEqual(slot.value, copy.value)
        self.assertEqual(slot.slot_type, copy.slot_type)
        self.assertEqual(slot.attributes, copy.attributes)

    def test_slot_copy_does_not_copy_fact(self):
        slot = Slot(self.to_value, self.attributes, self.fact)
        copy = slot.copy()

        self.assertIsNone(copy.fact)

    def test_slot_copy_changes_to_original_do_not_reflect_to_copy(self):
        slot = Slot(self.to_value, self.attributes, self.fact)
        copy = slot.copy()
        slot.attributes["new_key"] = "new_val"
        slot.value = LiteralSource("new literal")

        self.assertNotEqual(slot.value, copy.value)
        self.assertNotEqual(slot.attributes, copy.attributes)

    def test_slot_copy_changes_to_copy_do_not_reflect_to_original(self):
        slot = Slot(self.to_value, self.attributes, self.fact)
        copy = slot.copy()
        copy.attributes["new_key"] = "new_val"
        copy.value = LiteralSource("new literal")

        self.assertNotEqual(slot.value, copy.value)
        self.assertNotEqual(slot.attributes, copy.attributes)


class TestLiteralSlot(TestCase):
    def setUp(self):
        self.attributes = dict()

    def test_literal_slot_creation_with_defaults(self):
        slot = LiteralSlot("a string")
        self.assertEqual(slot.value, "a string")
        self.assertIsInstance(slot.attributes, dict)
        self.assertEqual(len(slot.attributes), 0)
        self.assertEqual(slot.slot_type, "literal")

    def test_literal_slot_creation_without_defaults(self):
        slot = LiteralSlot("a string", self.attributes)
        self.assertEqual(slot.attributes, self.attributes)


class TestSlotSource(TestCase):
    def setUp(self):
        self.fact = Fact(
            "corpus name",
            "corpus_type",
            "timestamp_from",
            "timestamp_to",
            "timestamp_type",
            "analysis_type",
            "result_key",
            "result_value",
            "outlierness",
        )
        self.source = SlotSource("field")

    def test_slot_source_creation(self):
        self.assertEqual(self.source.field_name, "field")

    def test_slot_source_is_abstract(self):
        with self.assertRaises(NotImplementedError):
            self.source(self.fact)


class TestFactFieldSource(TestCase):
    def setUp(self):
        self.fact = Fact(
            "corpus name",
            "corpus_type",
            "timestamp_from",
            "timestamp_to",
            "timestamp_type",
            "analysis_type",
            "result_key",
            "result_value",
            "outlierness",
        )
        self.message = Message(self.fact, 0.1, 0.2, 0.3)
        self.source = FactFieldSource("corpus")

    def test_fact_field_source_creation(self):
        self.assertEqual(self.source.field_name, "corpus")

    def test_fact_field_source_retrieves_from_fact_on_call(self):
        self.assertEqual(self.source(self.fact), "corpus name")


class TestLiteralSource(TestCase):
    def setUp(self):
        self.fact = Fact(
            "corpus name",
            "corpus_type",
            "timestamp_from",
            "timestamp_to",
            "timestamp_type",
            "analysis_type",
            "result_key",
            "result_value",
            "outlierness",
        )
        self.source = LiteralSource("Some literal")

    def test_literal_source_creation(self):
        self.assertEqual(self.source.value, "Some literal")
        self.assertEqual(self.source.field_name, "literal")

    def test_literal_source_ignores_fact_and_always_returns_literal(self):
        self.assertEqual(self.source(self.fact), "Some literal")


class TestTimeSource(TestCase):
    def setUp(self):
        self.fact = Fact("_", "_", "t1", "t2", "tt", "_", "_", "_", "_")
        self.source = TimeSource()

    def test_time_source_creation(self):
        self.assertEqual(self.source.field_name, "time")

    def test_time_source_retrieves_from_fact(self):
        self.assertEqual(self.source(self.fact), "[TIME:tt:t1:t2]")


class TestLhsExpr(TestCase):
    def setUp(self):
        self.fact = self.fact = Fact("_", "_", "_", "_", "_", "_", "_", "_", "_")
        self.expr = LhsExpr()

    def test_lhs_expr_is_abstract(self):
        with self.assertRaises(NotImplementedError):
            self.expr(self.fact, [self.fact])

        with self.assertRaises(NotImplementedError):
            str(self.expr)


class TestFactField(TestCase):
    def setUp(self):
        self.fact1 = Fact("1", "_", "_", "_", "_", "_", "_", "_", "_")
        self.fact2 = Fact("2", "_", "_", "_", "_", "_", "_", "_", "_")
        self.all_facts = [self.fact1, self.fact2]
        self.field = FactField("corpus")

    def test_fact_field_creation(self):
        self.assertEqual(self.field.field_name, "corpus")

    def test_fact_field_fetches_from_fact(self):
        self.assertEqual(self.field(self.fact1, self.all_facts), "1")


class TestReferentialExpr(TestCase):
    def setUp(self):
        self.fact1 = Fact("1", "_", "_", "_", "_", "_", "_", "_", "_")
        self.fact2 = Fact("2", "_", "_", "_", "_", "_", "_", "_", "_")
        self.all_facts = [self.fact1, self.fact2]
        self.expr = ReferentialExpr(1, "corpus")

    def test_referential_expr_creation(self):
        self.assertEqual(self.expr.field_name, "corpus")
        self.assertEqual(self.expr.reference_idx, 1)

    def test_referential_expr_fetches_from_correct_fact(self):
        self.assertEqual(self.expr(self.fact1, self.all_facts), "2")


class TestMatcher(TestCase):
    def setUp(self):
        self.fact1 = Fact("1", "_", "_", "_", "_", "_", "_", "_", "_")
        self.fact2 = Fact("2", "_", "_", "_", "_", "_", "_", "_", "_")
        self.all_facts = [self.fact1, self.fact2]
        self.expr = FactField("corpus")

    def test_matcher_standard_ops_map_correctly(self):
        import operator

        self.assertEqual(Matcher.OPERATORS["!="], operator.ne)
        self.assertEqual(Matcher.OPERATORS[">"], operator.gt)
        self.assertEqual(Matcher.OPERATORS["<"], operator.lt)
        self.assertEqual(Matcher.OPERATORS[">="], operator.ge)
        self.assertEqual(Matcher.OPERATORS["<="], operator.le)

    def test_matcher_equals_op(self):
        equals = Matcher.OPERATORS["="]
        self.assertTrue(equals(1, 1))
        self.assertTrue(equals(1, "1"))
        self.assertTrue(equals("1", "1"))
        self.assertTrue(equals(None, None))

        self.assertFalse(equals(1, "2"))
        self.assertFalse(equals(1, 2))
        self.assertFalse(equals(1, None))
        self.assertFalse(equals("1", "2"))

    def test_correctly_applies_check_to_fact_non_callable(self):
        matcher = Matcher(self.expr, "=", "1")
        self.assertTrue(matcher(self.fact1, self.all_facts))
        self.assertFalse(matcher(self.fact2, self.all_facts))

    def test_correctly_applies_check_to_fact_callable(self):
        matcher = Matcher(self.expr, "=", lambda x, y: "2")
        self.assertTrue(matcher(self.fact2, self.all_facts))
        self.assertFalse(matcher(self.fact1, self.all_facts))


class TestTemplate(TestCase):
    def setUp(self):
        self.fact1 = Fact("1", "_", "_", "_", "_", "_", "_", "_", "_")
        self.fact2 = Fact("2", "_", "_", "_", "_", "_", "_", "_", "_")

        self.message1 = Message(self.fact1)
        self.message2 = Message(self.fact2)

        self.expr = FactField("corpus")
        self.matcher = Matcher(self.expr, "=", "1")
        self.rules = [([self.matcher], [0])]

        self.slot = Slot(SlotSource("corpus"))
        self.literal = LiteralSlot("literal")
        self.components = [self.slot, self.literal]

        self.template = Template(self.components, self.rules)

    def test_template_constructs(self):
        self.assertListEqual(self.template.components, self.components)
        self.assertIsInstance(self.template.facts, list)
        self.assertEqual(len(self.template.facts), 0)

    def test_template_sets_parent_to_components(self):
        self.assertEqual(self.slot.parent, self.template)
        self.assertEqual(self.literal.parent, self.template)

    def test_template_get_slot(self):
        self.assertEqual(self.template.get_slot("corpus"), self.slot)
        self.assertEqual(self.template.get_slot("literal"), self.literal)

        with self.assertRaises(KeyError):
            self.template.get_slot("no such")

    def test_template_add_slot(self):
        new_slot = Slot(SlotSource("timestamp_from"))
        self.template.add_slot(2, new_slot)
        self.assertIn(new_slot, self.template.components)
        self.assertEqual(self.template.get_slot("timestamp_from"), new_slot)

    def test_template_added_slot(self):
        new_slot = Slot(SlotSource("timestamp_from"))
        self.template.add_slot(1, new_slot)
        self.assertListEqual(self.template.components, [self.slot, new_slot, self.literal])

    def test_template_added_slot_is_last_component(self):
        new_slot = Slot(SlotSource("timestamp_from"))
        self.template.add_slot(2, new_slot)
        self.assertListEqual(self.template.components, [self.slot, self.literal, new_slot])

    def test_template_move_slot_forwards(self):
        # TODO: This fails, when it shouldn't
        new_slot = Slot(SlotSource("timestamp_from"))
        self.template.add_slot(2, new_slot)

        self.template.move_slot(0, 1)
        self.assertListEqual(self.template.components, [self.literal, self.slot, new_slot])

    def test_template_move_slot_backwards(self):
        new_slot = Slot(SlotSource("timestamp_from"))
        self.template.add_slot(2, new_slot)

        self.template.move_slot(2, 1)
        self.assertListEqual(self.template.components, [self.slot, new_slot, self.literal])

    def test_template_check_success(self):
        used_facts = self.template.check(self.message1, [self.message1])
        self.assertEqual(len(used_facts), 1)
        self.assertIn(self.fact1, used_facts)

    def test_template_check_success_does_not_fill(self):
        self.template.check(self.message1, [self.message1])
        self.assertIsNone(self.message1.template)
        self.assertEqual(len(self.template.facts), 0)
        self.assertIsNone(self.slot.fact)

    def test_template_check_failure(self):
        used_facts = self.template.check(self.message2, [self.message2])
        self.assertEqual(len(used_facts), 0)
        self.assertNotIn(self.fact2, used_facts)

    def test_template_check_failure_does_not_fill(self):
        self.template.check(self.message2, [self.message2])
        self.assertEqual(len(self.template.facts), 0)
        self.assertIsNone(self.slot.fact)

    def test_template_fill_success(self):
        used_facts = self.template.fill(self.message1, [self.message1])
        self.assertEqual(len(used_facts), 1)
        self.assertIn(self.fact1, used_facts)

    def test_template_fill_success_fills(self):
        self.template.fill(self.message1, [self.message1])
        self.assertEqual(len(self.template.facts), 1)
        self.assertIn(self.fact1, self.template.facts)
        self.assertEqual(self.slot.fact, self.fact1)

    def test_template_fill_failure(self):
        used_facts = self.template.fill(self.message2, [self.message2])
        self.assertEqual(len(used_facts), 0)
        self.assertNotIn(self.fact2, used_facts)

    def test_template_fill_failure_does_not_fill(self):
        self.template.fill(self.message2, [self.message2])
        self.assertEqual(len(self.template.facts), 0)
        self.assertIsNone(self.slot.fact)

    # TODO: Add tests for more complex templates, i.e. \w multiple Matchers and multiple Messages


if __name__ == "__main__":
    main()
