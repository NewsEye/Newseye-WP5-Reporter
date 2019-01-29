from unittest import main, TestCase
from reporter.core.models import Message, Fact, DocumentPlanNode, Document, Relation, TemplateComponent, Slot, \
    LiteralSource, SlotSource, LiteralSlot, FactFieldSource


class TestFact(TestCase):

    def setUp(self):
        self.fact = Fact('corpus', 'corpus_type', 'timestamp_from', 'timestamp_to', 'timestamp_type', 'analysis_type',
                         'result_key', 'result_value', 'outlierness')

    def test_fact_fields(self):
        self.assertEqual(self.fact.corpus, 'corpus')
        self.assertEqual(self.fact.corpus_type, 'corpus_type')
        self.assertEqual(self.fact.timestamp_from, 'timestamp_from')
        self.assertEqual(self.fact.timestamp_to, 'timestamp_to')
        self.assertEqual(self.fact.timestamp_type, 'timestamp_type')
        self.assertEqual(self.fact.analysis_type, 'analysis_type')
        self.assertEqual(self.fact.result_key, 'result_key')
        self.assertEqual(self.fact.result_value, 'result_value')
        self.assertEqual(self.fact.outlierness, 'outlierness')


class TestMessage(TestCase):

    def setUp(self):
        self.fact1 = Fact('corpus1', 'corpus_type', 'timestamp_from', 'timestamp_to', 'timestamp_type', 'analysis_type',
                          'result_key', 'result_value', 'outlierness')
        self.fact2 = Fact('corpus2', 'corpus_type', 'timestamp_from', 'timestamp_to', 'timestamp_type', 'analysis_type',
                          'result_key', 'result_value', 'outlierness')

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
        self.fact1 = Fact('corpus1', 'corpus_type', 'timestamp_from', 'timestamp_to', 'timestamp_type', 'analysis_type',
                          'result_key', 'result_value', 'outlierness')
        self.message1 = Message(self.fact1, 0.1, 0.2, 0.3)

        self.fact2 = Fact('corpus2', 'corpus_type', 'timestamp_from', 'timestamp_to', 'timestamp_type', 'analysis_type',
                          'result_key', 'result_value', 'outlierness')
        self.message2 = Message(self.fact2, 0.1, 0.2, 0.3)
        self.document_plan_node = DocumentPlanNode([self.message1, self.message2], Relation.ELABORATION)
        self.document = Document('en', self.document_plan_node)

    def test_document_creation(self):
        self.assertEqual(self.document.language, 'en')
        self.assertEqual(self.document.document_plan, self.document_plan_node)

    def test_document_messages_retrieves_all_messages(self):
        self.assertIn(self.message1, self.document.messages())
        self.assertIn(self.message2, self.document.messages())


class TestDocumentPlanNode(TestCase):

    def setUp(self):
        self.fact1 = Fact('corpus1', 'corpus_type', 'timestamp_from', 'timestamp_to', 'timestamp_type', 'analysis_type',
                          'result_key', 'result_value', 'outlierness')
        self.message1 = Message(self.fact1, 0.1, 0.2, 0.3)

        self.fact2 = Fact('corpus2', 'corpus_type', 'timestamp_from', 'timestamp_to', 'timestamp_type', 'analysis_type',
                          'result_key', 'result_value', 'outlierness')
        self.message2 = Message(self.fact2, 0.1, 0.2, 0.3)

        self.document_plan_node = DocumentPlanNode([self.message1, self.message2], Relation.ELABORATION)

    def test_document_plan_node_creation_sets_values(self):
        self.assertListEqual(self.document_plan_node.children, [self.message1, self.message2])
        self.assertEqual(self.document_plan_node.relation, Relation.ELABORATION)
        self.assertEqual(str(self.document_plan_node), 'ELABORATION')

    def test_document_plan_node_print_tree_does_not_crash(self):
        self.document_plan_node.print_tree()

if __name__ == '__main__':
    main()
