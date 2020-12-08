from abc import ABC, abstractmethod
from typing import List, Tuple, Type, Union, Dict

from reporter.core.models import Message
from reporter.core.realize_slots import SlotRealizerComponent
from reporter.newspaper_message_generator import TaskResult


class ProcessorResource(ABC):

    EPSILON = 0.00000001

    @abstractmethod
    def templates_string(self) -> str:
        pass

    @abstractmethod
    def parse_messages(self, task_result: TaskResult, context: List[TaskResult]) -> List[Message]:
        pass

    @abstractmethod
    def slot_realizer_components(self) -> List[Type[SlotRealizerComponent]]:
        pass

    def _parse_dataset(self, dataset) -> Tuple[List[str], List[str]]:
        print(dataset, type(dataset))
        corpus_type = ["dataset"]
        if isinstance(dataset, str):
            corpus = dataset
        else:
            corpus = dataset["name"]
        corpus = [corpus]
        return corpus_type, corpus

    def _parse_search_query(self, search_query) -> Tuple[List[str], List[str]]:
        corpus_type, corpus = ["query"], []
        q = search_query.get("q")
        if q:
            corpus.append(q)

        mm = search_query.get("mm")
        if mm:
            corpus.append("mm:{}".format(mm))

        fq = search_query.get("qf")
        if fq:
            corpus.append("qf:{}".format(fq))

        return corpus_type, corpus

    def _parse_corpus_fields(self, task_result: Union[Dict, TaskResult]) -> Tuple[List[str], List[str]]:
        corpus = []
        corpus_type = []

        if isinstance(task_result, TaskResult):
            dataset = task_result.dataset
            search_query = task_result.search_query
        else:
            dataset = task_result.get("dataset")
            search_query = task_result.get("search_query")

        if dataset:
            new_corpus_type, new_corpus = self._parse_dataset(dataset)
            corpus.extend(new_corpus)
            corpus_type.extend(new_corpus_type)

        if search_query:
            new_corpus_type, new_corpus = self._parse_search_query(search_query)
            corpus.extend(new_corpus)
            corpus_type.extend(new_corpus_type)

        return corpus_type, corpus

    def build_corpus_fields(self, task_result: Union[Dict, TaskResult]) -> Tuple[str, str]:
        if isinstance(task_result, TaskResult) and task_result.collection1:
            corpus_type = "multicorpus_comparison"
            corpus1, corpus1_type = self.build_corpus_fields(task_result.collection1)
            corpus1 = corpus1[1:-1]  # Remove parens
            corpus2, corpus2_type = self.build_corpus_fields(task_result.collection2)
            corpus2 = corpus2[1:-1]  # Remove parens
            corpus = f"[{corpus_type}:{corpus1}||{corpus2}]"
        else:
            corpus_type, corpus = self._parse_corpus_fields(task_result)
            corpus_type = "_".join(corpus_type)
            print(corpus)
            if corpus_type == "dataset_query" and len(corpus) > 2:
                corpus = f"[{corpus_type}:{corpus[0]}:{corpus[1]}:{'|'.join(corpus[2:])}]"
            elif corpus_type == "query" and len(corpus) > 1:
                corpus = f"[{corpus_type}:{corpus[0]}:{'|'.join(corpus[1:])}]"
            else:
                corpus = f"[{corpus_type}:{'|'.join(corpus)}]"
        return corpus, corpus_type
