import json
import logging
import os
from random import Random
from typing import Any, Dict, List, Tuple, Union

from reporter.core import Fact, NoMessagesForSelectionException, NLGPipelineComponent, Message, Registry

log = logging.getLogger('root')


class NewspaperMessageGenerator(NLGPipelineComponent):

    def __init__(self) -> None:
        self.MESSAGE_GENERATORS = [
            self._common_facet_values_message_generator,
            self._find_steps_from_time_series_message_generator,
            self._extract_facets_message_generator,
        ]

    def run(self, registry: Registry, random: Random, language: str, data:str) -> Tuple[List[Message]]:
        """
        Run this pipeline component.
        """
        if not data: raise NoMessagesForSelectionException('No data at all!')
        results = json.loads(data)['root']
        task_results = [TaskResult.from_dict(a) for a in results]
        analyses = []  # Type: List[TaskResult]
        for result in task_results:
            if result.children:
                task_results.extend(result.children)
            if result.task_type == 'analysis':
                analyses.append(result)

        messages = []  # Type: List[Message]
        for analysis in analyses:
            for message_generator in self.MESSAGE_GENERATORS:
                new_messages = message_generator(analysis)
                for msg in new_messages:
                    log.debug('Generated message {}'.format(msg))
                if new_messages:
                    messages.extend(new_messages)
                else:
                    log.error("Failed to parse a Message from {}. Utility={}".format(analysis, analysis.task_parameters.get('utility')))

        if not messages:
            raise NoMessagesForSelectionException()

        return (messages, )

    def _common_facet_values_message_generator(self, analysis: 'TaskResult') -> List[Message]:
        if analysis.task_parameters.get('utility') != 'common_facet_values':
            return []

        corpus_type = 'query_result'
        corpus = '[q:{}]'.format(analysis.task_parameters['target_search']['q'])

        messages = []
        for idx, result in enumerate(analysis.task_result['facet_counts']):
            count = result['document_count']
            facet_type = analysis.task_parameters['facet_name']
            facet_value = result['facet_value']
            interestingness = analysis.task_result['interestingness'][idx]
            messages.append(
                Message(
                    # TODO: This needs to be a list for the thing not to crash despite efforts to allow non-lists, see Message
                    [Fact(
                        corpus,  # corpus
                        corpus_type,  # corpus_type'
                        None,  # timestamp_from
                        None,  # timestamp_to
                        'all_time',  # timestamp_type
                        'facet_count',  # analysis_type
                        "[{}:{}]".format(facet_type, facet_value),  # result_key
                        count,  # result_value
                        interestingness,  # outlierness
                    )]
                )
            )
        return messages

    def _extract_facets_message_generator(self, analysis: 'TaskResult') -> List[Message]:
        if analysis.task_parameters.get('utility') != 'extract_facets':
            return []

        corpus_type = 'query_result'
        corpus = '[q:{}]'.format(analysis.task_parameters['target_search']['q'])

        messages = []
        for facet, values_and_counts in analysis.task_result.items():
            if 'example' in facet: continue
            for facet_value, count in values_and_counts.items():
                messages.append(
                    Message(
                        # TODO: This needs to be a list for the thing not to crash despite efforts to allow non-lists, see Message
                        [Fact(
                            corpus,  # corpus
                            corpus_type,  # corpus_type'
                            None,  # timestamp_from
                            None,  # timestamp_to
                            'all_time',  # timestamp_type
                            'facet_count_{}'.format(facet),  # analysis_type
                            "[{}:{}]".format(facet, facet_value),  # result_key
                            count,  # result_value
                            5,  # outlierness
                        )]
                    )
            )
        return messages

    def _find_steps_from_time_series_message_generator(self, analysis: 'TaskResult') -> List[Message]:
        if analysis.task_parameters.get('utility') != 'find_steps_from_time_series':
            return []

        corpus_type = 'query_result'
        corpus = '[q:{}]'.format(analysis.task_parameters['target_search']['q'])

        messages = []
        for facet_value, result in analysis.task_result.items():
            if not result: continue
            facet_type = analysis.task_parameters['facet_name']
            year = result[0][0]
            before = result[0][1][0] * 100
            after = result[0][1][1] * 100
            variance = result[0][2]
            interestingness = (abs(before - after) / variance) if variance != 0 else 0.000001
            messages.append(
                Message(
                    # TODO: This needs to be a list for the thing not to crash despite efforts to allow non-lists, see Message
                    [Fact(
                        corpus,  # corpus
                        corpus_type,  # corpus_type'
                        '[year:{}]'.format(year),  # timestamp_from
                        '[year:{}]'.format(year),  # timestamp_to
                        'year',  # timestamp_type
                        'step_detection',  # analysis_type
                        "[{}:{}]".format(facet_type, facet_value),  # result_key
                        '[CHANGE:{}:{}]'.format(before, after),  # result_value
                        interestingness,  # outlierness
                    )]
                )
            )
        return messages


class TaskResult(object):
    def __init__(self,
                 children: List['TaskResult'],
                 hist_parent_id: str,
                 task_parameters: Dict[str, Any],
                 task_result: Any,
                 task_type: str,
                 uuid: str) -> None:
        self.children = children
        self.hist_parent_id = hist_parent_id
        self.task_parameters = task_parameters
        self.task_result = task_result
        self.task_type = task_type
        self.uuid = uuid

    @staticmethod
    def from_dict(json: Dict[str, Any]) -> 'TaskResult':
        return TaskResult(
            [TaskResult.from_dict(child) for child in json['children']] if 'children' in json else [],
            json['hist_parent_id'],
            json['task_parameters'],
            json['task_result'],
            json['task_type'],
            json['uuid']
        )
