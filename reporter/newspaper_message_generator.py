import json
import logging
from random import Random
from typing import Any, Dict, List, Tuple, Optional

from reporter.core import (
    Fact,
    NoMessagesForSelectionException,
    NLGPipelineComponent,
    Message,
    Registry,
)

log = logging.getLogger("root")


class NewspaperMessageGenerator(NLGPipelineComponent):
    def __init__(self) -> None:
        self.MESSAGE_GENERATORS = [
            self._common_facet_values_message_generator,
            self._find_steps_from_time_series_message_generator,
            self._extract_facets_message_generator,
            self._query_topic_model_topic_weights_message_generator,
            self._compute_tf_idf_message_generator,
        ]

    def run(
        self, registry: Registry, random: Random, language: str, data: str
    ) -> Tuple[List[Message]]:
        """
        Run this pipeline component.
        """
        if not data:
            raise NoMessagesForSelectionException("No data at all!")
        results = json.loads(data)["root"]
        task_results = [TaskResult.from_dict(a) for a in results]
        analyses = []  # Type: List[TaskResult]
        for result in task_results:
            if result.children:
                task_results.extend(result.children)
            if result.task_type == "analysis":
                analyses.append(result)

        messages = []  # Type: List[Message]
        for analysis in analyses:
            found_new = False
            for message_generator in self.MESSAGE_GENERATORS:
                try:
                    new_messages = message_generator(analysis, analyses)
                    for msg in new_messages:
                        log.debug("Generated message {}".format(msg))
                    if new_messages:
                        found_new = True
                        messages.extend(new_messages)
                except Exception as ex:
                    log.error("Message generator crashed: {}".format(ex), exc_info=True)
            if not found_new:
                log.error(
                    "Failed to parse a Message from {}. Utility={}".format(
                        analysis, analysis.task_parameters.get("utility")
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

    def _common_facet_values_message_generator(
        self, analysis: "TaskResult", other_analyses: List["TaskResult"]
    ) -> List[Message]:
        if analysis.task_parameters.get("utility") != "common_facet_values":
            return []

        corpus, corpus_type = self._build_corpus_fields(analysis, other_analyses)

        messages = []
        for result, interestingness in zip(
            analysis.task_result["result"], analysis.task_result["interestingness"]
        ):
            count = result["document_count"]
            facet_type = analysis.task_parameters["utility_parameters"]["facet_name"]
            facet_value = result["facet_value"]
            messages.append(
                Message(
                    # TODO: This needs to be a list for the thing not to crash despite efforts to allow non-lists, see Message
                    [
                        Fact(
                            corpus,  # corpus
                            corpus_type,  # corpus_type'
                            None,  # timestamp_from
                            None,  # timestamp_to
                            "all_time",  # timestamp_type
                            "facet_count",  # analysis_type
                            "[{}:{}]".format(facet_type, facet_value),  # result_key
                            count,  # result_value
                            interestingness * 5,  # outlierness
                        )
                    ]
                )
            )
        return messages

    def _extract_facets_message_generator(
        self, analysis: "TaskResult", other_analyses: List["TaskResult"]
    ) -> List[Message]:
        if analysis.task_parameters.get("utility") != "extract_facets":
            return []

        corpus, corpus_type = self._build_corpus_fields(analysis, other_analyses)

        messages = []
        for (facet, facet_values_and_counts), (_, interestingness_values) in zip(
            analysis.task_result["result"].items(), analysis.task_result["interestingness"].items()
        ):
            for (facet_value, count), (_, interestingess) in zip(
                facet_values_and_counts.items(), interestingness_values.items()
            ):
                messages.append(
                    Message(
                        # TODO: This needs to be a list for the thing not to crash despite efforts to allow non-lists, see Message
                        [
                            Fact(
                                corpus,  # corpus
                                corpus_type,  # corpus_type'
                                None,  # timestamp_from
                                None,  # timestamp_to
                                "all_time",  # timestamp_type
                                "facet_count_{}".format(facet),  # analysis_type
                                "[{}:{}]".format(facet, facet_value),  # result_key
                                count,  # result_value
                                interestingess,  # outlierness
                            )
                        ]
                    )
                )
        return messages

    def _find_steps_from_time_series_message_generator(
        self, analysis: "TaskResult", other_analyses: List["TaskResult"]
    ) -> List[Message]:
        if analysis.task_parameters.get("utility") != "find_steps_from_time_series":
            return []

        parent = self._get_parent(analysis, other_analyses)
        corpus, corpus_type = self._build_corpus_fields(analysis, other_analyses)

        messages = []
        for result, interest in zip(
            analysis.task_result["result"], analysis.task_result["interestingness"]
        ):
            facet_type = parent.task_parameters["utility_parameters"]["facet_name"]
            facet_value = result["column"]
            for step, step_interestingess in zip(result["steps"], interest["steps"]):
                year = step["step_time"]
                before = step["step_start"]
                after = step["step_end"]
                error = step["step_error"]
                interestingness = (abs(before - after) / error) if error != 0 else 0.0000001
                messages.append(
                    Message(
                        # TODO: This needs to be a list for the thing not to crash despite efforts to allow non-lists, see Message
                        [
                            Fact(
                                corpus,  # corpus
                                corpus_type,  # corpus_type'
                                "[year:{}]".format(year),  # timestamp_from
                                "[year:{}]".format(year),  # timestamp_to
                                "year",  # timestamp_type
                                "step_detection",  # analysis_type
                                "[{}:{}]".format(facet_type, facet_value),  # result_key
                                "[CHANGE:{}:{}]".format(
                                    round(before, 2), round(after, 2)
                                ),  # result_value
                                interestingness,  # outlierness
                            )
                        ]
                    )
                )
        return messages

    def _query_topic_model_topic_weights_message_generator(
        self, analysis: "TaskResult", other_analyses: List["TaskResult"]
    ) -> List[Message]:
        if analysis.task_parameters.get("utility") != "query_topic_model":
            return []

        corpus, corpus_type = self._build_corpus_fields(analysis, other_analyses)

        model_type = analysis.task_parameters.get("utility_parameters", {}).get("model_type")
        model_name = analysis.task_parameters.get("utility_parameters", {}).get("model_name")

        messages = []
        for (topic_idx, topic_weight), topic_weight_interestingess in zip(
            enumerate(analysis.task_result["result"]["topic_weights"]),
            analysis.task_result["interestingness"]["topic_weights"],
        ):

            messages.append(
                Message(
                    # TODO: This needs to be a list for the thing not to crash despite efforts to allow non-lists, see Message
                    [
                        Fact(
                            corpus,  # corpus
                            corpus_type,  # corpus_type
                            None,  # timestamp_from
                            None,  # timestamp_to
                            "all_time",  # timestamp_type
                            "topic_weight",  # analysis_type
                            "[TOPIC:{}:{}:{}]".format(
                                model_type, model_name, topic_idx
                            ),  # result_key
                            "[TOPIC_WEIGHT:{}]".format(topic_weight),  # result_value
                            topic_weight_interestingess,  # outlierness
                        )
                    ]
                )
            )
        return messages

    def _compute_tf_idf_message_generator(
        self, analysis: "TaskResult", other_analyses: List["TaskResult"]
    ) -> List[Message]:
        if analysis.task_parameters.get("utility") != "compute_tf_idf":
            return []

        corpus, corpus_type = self._build_corpus_fields(analysis, other_analyses)

        interestingness_values = analysis.task_result["interestingness"]

        messages = []
        for word, counts in analysis.task_result["result"].items():
            if word not in interestingness_values:
                continue
            for count_key in ["count", "ipm", "tfidf"]:
                messages.append(
                    Message(
                        # TODO: This needs to be a list for the thing not to crash despite efforts to allow non-lists, see Message
                        [
                            Fact(
                                corpus,  # corpus
                                corpus_type,  # corpus_type'
                                None,  # timestamp_from
                                None,  # timestamp_to
                                "all_time",  # timestamp_type
                                "word_{}".format(count_key),  # analysis_type
                                "[WORD:{}]".format(word),  # result_key
                                counts[count_key],  # result_value
                                interestingness_values.get(word, 0),  # outlierness
                            )
                        ]
                    )
                )
        return messages

    def _get_parent(
        self, analysis: "TaskResult", other_analyses: List["TaskResult"]
    ) -> Optional["TaskResult"]:
        parent_uuid = analysis.hist_parent_id
        if not parent_uuid:
            return None

        for other in other_analyses:
            if other.uuid == parent_uuid:
                return other

        return None

    def _build_corpus_fields(
        self, analysis: "TaskResult", other_analyses: List["TaskResult"]
    ) -> Tuple[str, str]:
        while not analysis.task_parameters.get("search_query"):
            analysis = self._get_parent(analysis, other_analyses)
            if not analysis:
                return "full_corpus", "full_corpus"

        corpus = []
        corpus_type = []

        q = analysis.task_parameters.get("search_query", {}).get("q")
        if q:
            corpus.append("[q:{}]".format(q))
            corpus_type.append("query")

        mm = analysis.task_parameters.get("search_query", {}).get("mm")
        if mm:
            corpus.append("[mm:{}]".format(mm))
            corpus_type.append("minmatches")

        fq = analysis.task_parameters.get("search_query", {}).get("fq")
        if fq:
            corpus.append("[fq:{}]".format(fq))
            corpus_type.append("filter")

        return " ".join(corpus), "_".join(corpus_type)


class TaskResult(object):
    def __init__(
        self,
        children: List["TaskResult"],
        hist_parent_id: str,
        task_parameters: Dict[str, Any],
        task_result: Any,
        task_type: str,
        uuid: str,
    ) -> None:
        self.children = children
        self.hist_parent_id = hist_parent_id
        self.task_parameters = task_parameters
        self.task_result = task_result
        self.task_type = task_type
        self.uuid = uuid

    @staticmethod
    def from_dict(json: Dict[str, Any]) -> "TaskResult":
        return TaskResult(
            [TaskResult.from_dict(child) for child in json["children"]]
            if "children" in json
            else [],
            json.get("hist_parent_id"),
            json.get("task_parameters"),
            json.get("task_result"),
            json.get("task_type"),
            json.get("uuid"),
        )
