import logging
from typing import List

from reporter.core import Message, Fact
from reporter.newspaper_message_generator import TaskResult
from reporter.resources.processor_resource import ProcessorResource


log = logging.getLogger("root")


TEMPLATE = """
en: {result_key} appeared {result_value} times
fi: {result_key} esiintyi {result_value} kertaa
| analysis_type = ExtractWords:Count

en: {result_key} had a relative count of {result_value}
en: {result_key, case=gen} relative count was {result_value}
fi: {result_key, case=gen} suhteellinen osuus kaikista saneista oli {result_value}
| analysis_type = ExtractWords:RelativeCount

en: {result_key} had a TF-IDF score of {result_value} 
en: {result_key, case=gen} TF-IDF was {result_value}
fi: {result_key, case=gen} TF-IDF -luku oli {result_value}
| analysis_type = ExtractWords:TFIDF
"""


class ExtractWordsResource(ProcessorResource):

    def templates_string(self) -> str:
        return TEMPLATE

    def parse_messages(self, task_result: TaskResult, context: List[TaskResult]) -> List[Message]:
        if not task_result.processor == "ExtractWords":
            return []

        if task_result.parameters.get("unit") != "tokens":
            log.error("Unexpected unit '{}', expected 'tokens'".format(task_result.parameters.get("unit")))
            return []

        messages = []
        for word in task_result.task_result['result']['vocabulary']:
            for result_idx, result_name in enumerate(['Count', 'RelativeCount', 'TFIDF']):
                result = task_result.task_result["result"]["vocabulary"][word][result_idx]
                messages.append(
                    Message(
                        [
                            Fact(
                                # TODO: Add corpus and corpus_type parsing once investigator output is fixed
                                "UNKNOWN_CORPUS",  # corpus
                                "full_corpus",  # corpus_type
                                None,  # timestamp_from
                                None,  # timestamp_to
                                "all_time",  # timestamp_type
                                "ExtractWords:" + result_name,  # analysis_type
                                "[TOKEN:{}]".format(word),  # result_key
                                result,  # result_value
                                task_result.task_result['interestingness'].get(word, ProcessorResource.EPSILON)  # outlierness
                            )
                        ]
                    )
                )
        return messages

