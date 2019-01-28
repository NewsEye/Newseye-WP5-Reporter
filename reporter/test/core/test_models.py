from unittest import main, TestCase
from reporter.core.models import Message, Fact


class TestFact(TestCase):
    def test_fact_fields(self):
        f = Fact('corpus', 'corpus_type', 'timestamp_from', 'timestamp_to', 'timestamp_type', 'analysis_type',
                 'result_key', 'result_value', 'outlierness')
        assert f.corpus == 'corpus'
        assert f.corpus_type == 'corpus_type'
        assert f.timestamp_from == 'timestamp_from'
        assert f.timestamp_to == 'timestamp_to'
        assert f.timestamp_type == 'timestamp_type'
        assert f.analysis_type == 'analysis_type'
        assert f.result_key == 'result_key'
        assert f.result_value == 'result_value'
        assert f.outlierness == 'outlierness'


class TestMessage(TestCase):

    def test_message_creation_single_fact(self):
        f = Fact('corpus', 'corpus_type', 'timestamp_from', 'timestamp_to', 'timestamp_type', 'analysis_type',
                 'result_key', 'result_value', 'outlierness')
        print(f)

        m = Message(f, 0.1, 0.2, 0.3)

        assert isinstance(m.facts, list) and not isinstance(m.facts, Fact)
        assert len(m.facts) == 1
        assert m.facts[0] == f
        assert m.main_fact == f
        assert m.importance_coefficient == 0.1
        assert m.score == 0.2
        assert m.polarity == 0.3
        assert m.template is None
        assert str(m) == "<Message>"

    def test_message_creation_list_of_facts(self):
        f1 = Fact('corpus1', 'corpus_type', 'timestamp_from', 'timestamp_to', 'timestamp_type', 'analysis_type',
                  'result_key', 'result_value', 'outlierness')
        f2 = Fact('corpus2', 'corpus_type', 'timestamp_from', 'timestamp_to', 'timestamp_type', 'analysis_type',
                  'result_key', 'result_value', 'outlierness')
        m = Message([f1, f2], 0.1, 0.2, 0.3)

        assert isinstance(m.facts, list)
        assert len(m.facts) == 2
        assert m.facts == [f1, f2]
        assert m.main_fact == f1

    def test_message_set_facts_always_list1(self):
        f1 = Fact('corpus1', 'corpus_type', 'timestamp_from', 'timestamp_to', 'timestamp_type', 'analysis_type',
                  'result_key', 'result_value', 'outlierness')
        f2 = Fact('corpus2', 'corpus_type', 'timestamp_from', 'timestamp_to', 'timestamp_type', 'analysis_type',
                  'result_key', 'result_value', 'outlierness')
        m = Message(f1, 0.1, 0.2, 0.3)

        assert m.facts == [f1]
        assert m.main_fact == f1

        m.facts = f2

        assert m.facts == [f2]
        assert m.main_fact == f2

    def test_message_set_facts_always_list2(self):
        f1 = Fact('corpus1', 'corpus_type', 'timestamp_from', 'timestamp_to', 'timestamp_type', 'analysis_type',
                  'result_key', 'result_value', 'outlierness')
        f2 = Fact('corpus2', 'corpus_type', 'timestamp_from', 'timestamp_to', 'timestamp_type', 'analysis_type',
                  'result_key', 'result_value', 'outlierness')
        m = Message(f2, 0.1, 0.2, 0.3)

        assert m.facts == [f2]
        assert m.main_fact == f2

        m.facts = [f1, f2]

        assert m.facts == [f1, f2]
        assert m.main_fact == f1


if __name__ == '__main__':
    main()
