from collections.abc import Iterable
from .pipeline import NLGPipelineComponent

import logging
log = logging.getLogger('root')


def filter_messages(messages, what_type=None, what=None, where_type=None, where=None):
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


def extend_or_append(collection, new_items):
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

    def run(self, *_):
        return ""


class PrintMessages(NLGPipelineComponent):

    def run(self, registry, messages):
        for m in messages:
            log.info(m)
        return ""


class PrintNuclei(NLGPipelineComponent):

    def run(self, registry, nuclei, non_nuclei):
        log.info("Nuclei:")
        for m in nuclei:
            print("\t{}".format(m))
        return ""


class PrintDocumentPlan(NLGPipelineComponent):

    def run(self, registry, dp, *args):
        log.info("Printing tree to stdout")
        print()
        dp.print_tree()
        print()
        return ""


class PrintOutput(NLGPipelineComponent):

    def run(self, registry, output):
        log.info("Printing output:")
        print("\n" + output + "\n")
        return ""
