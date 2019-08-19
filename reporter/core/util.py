from collections.abc import Iterable
import logging
from typing import Any, List, Optional, TypeVar, Union

from .models import DocumentPlanNode, Message
from .pipeline import NLGPipelineComponent
from .registry import Registry

log = logging.getLogger("root")


def filter_messages(
    messages: List[Message],
    what_type: Optional[str] = None,
    what: Optional[str] = None,
    where_type: Optional[str] = None,
    where: Optional[str] = None,
) -> List[Message]:
    """
    Filters a list of message so that only message that match the parameters are returned.
    """
    if what_type:
        messages = [m for m in messages if m.what_type == what_type]
    if what:
        messages = [m for m in messages if m.what == what]
    if where:
        messages = [m for m in messages if m.where == where]
    if where_type:
        messages = [m for m in messages if m.where_type == where_type]
    return messages


T = TypeVar("T")


def extend_or_append(collection: List[T], new_items: Union[T, List[T]]) -> List[T]:
    """
    Expands or appends 'new_items' to 'collection', depending on whether
    'new_items' is a collection or not.
    """
    if isinstance(new_items, Iterable):
        collection.extend(new_items)
    else:
        collection.append(new_items)
    return collection


class SquelchOutput(NLGPipelineComponent):
    def run(self, *_: Any) -> str:
        return ""


class PrintMessages(NLGPipelineComponent):
    def run(self, registry: Registry, messages: List[Message]) -> str:
        for m in messages:
            log.info(m)
        return ""


class PrintNuclei(NLGPipelineComponent):
    def run(self, registry: Registry, nuclei: List[Message], non_nuclei: List[Message]) -> str:
        log.info("Nuclei:")
        for m in nuclei:
            print("\t{}".format(m))
        return ""


class PrintDocumentPlan(NLGPipelineComponent):
    def run(self, registry: Registry, dp: DocumentPlanNode, *args: Any) -> str:
        log.info("Printing tree to stdout")
        print()
        dp.print_tree()
        print()
        return ""


class PrintOutput(NLGPipelineComponent):
    def run(self, registry: Registry, output: Any) -> str:
        log.info("Printing output:")
        print("\n" + output + "\n")
        return ""
