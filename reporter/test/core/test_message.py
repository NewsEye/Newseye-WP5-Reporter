from unittest import main, TestCase
from reporter.core.document import Message, Fact

class Test_Message(TestCase):

    def test_fact_creation(self):
        f = Fact('where', 'where_type', 'what', 'what_type', 'when_1', 'when_2', 'when_type', 0.5)
        assert f.where == 'where'
        assert f.where_type == 'where_type'
        assert f.what == 'what'
        assert f.what_type == 'what_type'
        assert f.when_1 == 'when_1'
        assert f.when_2 == 'when_2'
        assert f.when_type == 'when_type'
        assert f.outlierness == 0.5

    def test_message_creation(self):
        fact = Fact('where', 'where_type', 'what', 'what_type', 'when_1', 'when_2', 'when_type', 0.5)
        msg = Message(fact)
        assert msg.facts is list
        assert msg.facts[0] is fact
        assert msg.main_fact == fact
        assert msg.importance_coefficient == 1.0
        assert msg.score == 0.0
        assert msg.polarity == 0.0

        fact2 = Fact('where', 'where_type', 'what', 'what_type', 'when_1', 'when_2', 'when_type', 2)
        msg.facts = [fact, fact2]
        assert msg.facts is list
        assert fact in msg.facts
        assert fact2 in msg.facts

        assert msg.main_fact is fact

    def test_message_set_facts_always_list(self):
        fact = Fact('where', 'where_type', 'what', 'what_type', 'when_1', 'when_2', 'when_type', 0.5)
        msg = Message()
        assert len(msg.facts) == 0
        msg.fa

if __name__ == '__main__':
    main()