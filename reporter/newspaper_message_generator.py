import json
import logging
from random import Random
from typing import Any, Dict, List, Tuple

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
            found_new = False
            for message_generator in self.MESSAGE_GENERATORS:
                new_messages = message_generator(analysis, analyses)
                for msg in new_messages:
                    log.debug('Generated message {}'.format(msg))
                if new_messages:
                    found_new = True
                    messages.extend(new_messages)
            if not found_new:
                log.error("Failed to parse a Message from {}. Utility={}".format(analysis, analysis.task_parameters.get('utility')))

        # Filter out messages that share the same underlying fact. Can't be done with set() because of how the
        # __hash__ and __eq__ are (not) defined.
        facts = set()
        uniq_messages = []
        for m in messages:
            if m.main_fact not in facts:
                facts.add(m.main_fact)
                uniq_messages.append(m)
        messages = uniq_messages

        if not messages:
            raise NoMessagesForSelectionException()

        return (messages, )

    def _common_facet_values_message_generator(self, analysis: 'TaskResult', other_analyses: List['TaskResult']) -> List[Message]:
        if analysis.task_parameters.get('utility') != 'common_facet_values':
            return []

        corpus_type = 'query_result'
        corpus = '[q:{}]'.format(analysis.task_parameters['target_search']['q'])

        messages = []
        for result, interestingness in zip(analysis.task_result['result'], analysis.task_result['interestingness']):
            count = result['document_count']
            facet_type = analysis.task_parameters['utility_parameters']['facet_name']
            facet_value = result['facet_value']
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
                        interestingness * 5,  # outlierness
                    )]
                )
            )
        return messages

    def _extract_facets_message_generator(self, analysis: 'TaskResult', other_analyses: List['TaskResult']) -> List[Message]:
        if analysis.task_parameters.get('utility') != 'extract_facets':
            return []

        corpus_type = 'query_result'
        corpus = '[q:{}]'.format(analysis.task_parameters['target_search']['q'])

        messages = []
        for (facet, facet_values_and_counts), (_, interestingness_values) in zip(analysis.task_result['result'].items(), analysis.task_result['interestingness'].items()):
            for (facet_value, count), (_, interestingess) in zip(facet_values_and_counts.items(), interestingness_values.items()):
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
                            interestingess,  # outlierness
                        )]
                    )
            )
        return messages

    def _find_steps_from_time_series_message_generator(self, analysis: 'TaskResult', other_analyses: List['TaskResult']) -> List[Message]:
        if analysis.task_parameters.get('utility') != 'find_steps_from_time_series':
            return []

        corpus_type = 'query_result'

        parent: 'TaskResult' = next(task for task in other_analyses if task.uuid == analysis.task_parameters.get('target_uuid'))
        q = parent.task_parameters['target_search']['q']
        corpus = '[q:{}]'.format(parent.task_parameters['target_search']['q'])

        messages = []
        for result, interest in zip(analysis.task_result['result'], analysis.task_result['interestingness']):
            facet_type = parent.task_parameters['utility_parameters']['facet_name']
            facet_value = result['column']
            for step, step_interestingess in zip(result['steps'], interest['steps']):
                year = step['step_time']
                before = step['step_start']
                after = step['step_end']
                error = step['step_error']
                interestingness = (abs(before - after) / error) if error != 0 else 0.0000001
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
                            '[CHANGE:{}:{}]'.format(round(before, 2), round(after, 2)),  # result_value
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
            json.get('hist_parent_id'),
            json.get('task_parameters'),
            json.get('task_result'),
            json.get('task_type'),
            json.get('uuid')
        )
