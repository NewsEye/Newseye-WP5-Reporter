import json
import logging
import os
from random import Random
from typing import Any, Dict, List, Tuple, Union

from reporter.core import Fact, NoMessagesForSelectionException, NLGPipelineComponent, Message, Registry

log = logging.getLogger('root')


class NewspaperMessageGenerator(NLGPipelineComponent):

    def __init__(self) -> None:
        self.MESSAGE_GENERATORS = {
            'facet_counts': self._generate_messages_from_facet_counts,
            'common_topics': self._generate_messages_from_common_topics,
            'topic_analysis': self._ignore
        }

    def run(self, registry: Registry, random: Random, language: str, data:str) -> Tuple[List[Message]]:
        """
        Run this pipeline component.
        """
        if not data: raise NoMessagesForSelectionException('No data at all!')

        results = json.loads(data)['root']['children']

        analyses = []

        for child in results:
            query = Query(child['query'], child['query_id'])
            for analysis in child['analysis']:
                analyses.append(Analysis(
                    query,
                    analysis['analysis_type'],
                    analysis['analysis_result']
                ))

        messages = []
        for analysis in analyses:
            message_generator = self.MESSAGE_GENERATORS.get(analysis.type, None)
            if message_generator:
                messages.extend(message_generator(analysis))

        if not messages:
            raise NoMessagesForSelectionException()

        return (messages, )


    def _ignore(self, analysis: 'Analysis') -> List[Message]:
        return []

    def _print(self, analysis: 'Analysis') -> List[Message]:
        print('Query {} (ID={}): analysis_type={}, analysis_results={}'.format(
            analysis.query.values, analysis.query.id, analysis.type, analysis.result)
        )
        return []

    def _generate_messages_from_common_topics(self, analysis: 'Analysis') -> List[Message]:
        messages = []
        print(analysis.result)
        corpus_description = []
        for key, value in analysis.query.values.items():
            corpus_description.append("[{}:{}]".format(key, value))
        corpus_description = " ".join(corpus_description)
        for (topic, count) in analysis.result:
            messages.append(
                Message(
                    # TODO: This needs to be a list for the thing not to crash despite efforts to allow non-lists, see Message
                    [Fact(
                        corpus_description,  # corpus
                        'query_result',  # corpus_type'
                        None,  # timestamp_from
                        None,  # timestamp_to
                        'all_time',  # timestamp_type
                        'topic_count',  # analysis_type
                        "[TOPIC:{}]".format(topic),  # result_key
                        count,  # result_value
                        Random().randint(5,15),  # outlierness
                    )]
                )
            )
        return messages

    def _generate_messages_from_facet_counts(self, analysis: 'Analysis') -> List[Message]:
        messages = []
        print(analysis.result)
        corpus_description = []
        for key, value in analysis.query.values.items():
            corpus_description.append("[{}:{}]".format(key, value))
        corpus_description = " ".join(corpus_description)
        for facet in analysis.result:
            for entry in analysis.result[facet]:
                assert len(entry) == 2 # These are really 2-tuples of (str, int), even if they are in the JSON as lists
                key, count = entry
                messages.append(
                    Message(
                        # TODO: This needs to be a list for the thing not to crash despite efforts to allow non-lists, see Message
                        [Fact(
                            corpus_description, #corpus
                            'query_result', #corpus_type'
                            None, #timestamp_from
                            None, #timestamp_to
                            'all_time', #timestamp_type
                            'facet_count', #analysis_type
                            "[{}:{}]".format(facet, key), #result_key
                            count, #result_value
                            Random().randint(0,10), #outlierness
                        )]
                    )
                )
        return messages


class Query(object):
    def __init__(self, values: Dict[str, Any], id: str) -> None:
        self.values = values
        self.id = id


class Analysis(object):
    def __init__(self, query: Query, type: str, result: Dict[str, List[List[Union[int,str]]]]) -> None:
        self.query = query
        self.type = type
        self.result = result


if __name__ == '__main__':
    NewspaperMessageGenerator().run(None, None, '')