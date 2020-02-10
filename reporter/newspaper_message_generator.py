import json
import logging
from typing import Any, Dict, List, Tuple, Optional, Callable

from numpy.random import Generator

from reporter.core import (
    Fact,
    NoMessagesForSelectionException,
    NLGPipelineComponent,
    Message,
    Registry,
)

log = logging.getLogger("root")


class TaskResult:
    def __init__(
        self,
        uuid: str,
        search_query: Any,
        processor: str,
        parameters: Dict[str, Any],
        task_status: str,
        task_started: str,
        task_finished: str,
        task_result: Any
     ) -> None:
        self.uuid = uuid
        self.search_query = search_query
        self.processor = processor
        self.parameters = parameters
        self.task_status = task_status
        self.task_started = task_started
        self.task_finished = task_finished
        self.task_result = task_result

    @staticmethod
    def from_dict(o: Dict[str, Any]) -> "TaskResult":
        return TaskResult(
            o.get("uuid"),
            o.get("search_query"),
            o.get("processor"),
            o.get('parameters'),
            o.get('task_status'),
            o.get('task_started'),
            o.get('task_finished'),
            o.get('task_result'),
        )


class NewspaperMessageGenerator(NLGPipelineComponent):

    def run(
        self, registry: Registry, random: Generator, language: str, data: str
    ) -> Tuple[List[Message]]:
        """
        Run this pipeline component.
        """
        message_parsers: List[Callable[[TaskResult, List[TaskResult]], List[Message]]] = registry.get('message-parsers')

        if not data:
            raise NoMessagesForSelectionException("No data at all!")
        results = json.loads(data)
        task_results: List[TaskResult] = [TaskResult.from_dict(a) for a in results]

        messages: List[Message] = []
        for task_result in task_results:
            generation_succeeded = False
            for message_parser in message_parsers:
                try:
                    new_messages = message_parser(task_result, task_results)
                    for message in new_messages:
                        log.debug("Parsed message {}".format(message))
                    if new_messages:
                        generation_succeeded = True
                        messages.extend(new_messages)
                except Exception as ex:
                    log.error("Message parser crashed: {}".format(ex), exc_info=True)

            if not generation_succeeded:
                log.error(
                    "Failed to parse a Message from {}. Processor={}".format(
                        task_result, task_result.processor
                    )
                )

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

        return (messages,)