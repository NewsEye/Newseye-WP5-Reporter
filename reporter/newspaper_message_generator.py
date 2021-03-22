import json
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from numpy.random import Generator

from reporter.core.message_generator import NoMessagesForSelectionException
from reporter.core.models import Message
from reporter.core.pipeline import NLGPipelineComponent, Registry

log = logging.getLogger("root")


class TaskResult:
    def __init__(
        self,
        uuid: str,
        search_query: Any,
        dataset: Optional[str],
        collection1: Optional[Dict[str, Any]],
        collection2: Optional[Dict[str, Any]],
        processor: str,
        parameters: Dict[str, Any],
        task_status: str,
        task_started: str,
        task_finished: str,
        task_result: Any,
    ) -> None:
        self.uuid = uuid
        self.search_query = search_query
        self.dataset = dataset
        self.collection1 = collection1
        self.collection2 = collection2
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
            o.get("dataset"),
            o.get("collection1"),
            o.get("collection2"),
            o.get("processor"),
            o.get("parameters"),
            o.get("task_status"),
            o.get("task_started"),
            o.get("task_finished"),
            o.get("task_result"),
        )


PAYLOAD_LOGGING_PATH: Path = Path(__file__).parent / ".." / "errored_payloads"
MAX_LOGGED_PAYLOADS = 25


class NewspaperMessageGenerator(NLGPipelineComponent):
    def run(self, registry: Registry, random: Generator, language: str, data: str) -> Tuple[List[Message]]:
        """
        Run this pipeline component.
        """
        message_parsers: List[Callable[[TaskResult, List[TaskResult]], List[Message]]] = registry.get("message-parsers")

        if not data:
            raise NoMessagesForSelectionException("No data at all!")
        results = json.loads(data)
        task_results: List[TaskResult] = [TaskResult.from_dict(a) for a in results]

        messages: List[Message] = []
        for task_result, original_json in zip(task_results, results):
            log.info(f"Parsing messages from task result with id {task_result.uuid}")
            generation_succeeded = False
            for message_parser in message_parsers:
                try:
                    new_messages = message_parser(task_result, task_results, language)
                    for message in new_messages:
                        log.debug("Parsed message {}".format(message))
                    if new_messages:
                        generation_succeeded = True
                        messages.extend(new_messages)
                except Exception as ex:
                    log.error("Message parser crashed: {}".format(ex), exc_info=True)

            if not generation_succeeded:
                log.error("Failed to parse a Message from {}. Processor={}".format(task_result, task_result.processor))
                self.log_payload(original_json, task_result.uuid)

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

    @staticmethod
    def log_payload(payload: Dict, uuid: str) -> None:
        # Save payload as <uuid>.txt
        PAYLOAD_LOGGING_PATH.mkdir(parents=True, exist_ok=True)
        with (PAYLOAD_LOGGING_PATH / f"{uuid}.txt").open("w") as fp:
            json.dump(payload, fp)

        # Clean up older stored payload if there are more than 100.
        logged_payloads: List[Path] = list(PAYLOAD_LOGGING_PATH.glob("*.txt"))
        logged_payloads.sort(key=lambda path: path.stat().st_mtime, reverse=True)
        if len(logged_payloads) > MAX_LOGGED_PAYLOADS:
            for p in logged_payloads[MAX_LOGGED_PAYLOADS:]:
                p.unlink()
