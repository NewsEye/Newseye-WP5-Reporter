from enum import Enum

from .message import Message

import logging

log = logging.getLogger('root')


class Relation(Enum):
    """
    Defines possible relations between the children of a DocumentPlan node.
    """
    ELABORATION = 1
    EXEMPLIFICATION = 2
    CONTRAST = 3
    SEQUENCE = 4
    LIST = 5


class DocumentPlan(object):
    """
    Both the DocumentPlan an in general and a non-template, non-message node
    of the DocumentPlan tree.

    Contains an ordered list of children are connected by a relation.
    """

    def __init__(self, children=None, relation=Relation.SEQUENCE):
        if children is None:
            children = []
        self._children = children
        self._relation = relation

    @property
    def children(self):
        return self._children

    @property
    def relation(self):
        return self._relation

    def add_message(self, msg):
        self._children.append(msg)

    def __str__(self):
        return self.relation.name

    """
    Prints the DocumentPlan as a tree.
    Modified from http://stackoverflow.com/a/30893896
    """

    def print_tree(self, this=None, indent="", last='updown'):
        if not this:
            this = self

        def rec_count(node):
            count = 0
            if not isinstance(node, DocumentPlan):
                return count
            for child in node.children:
                count += 1 + rec_count(child)
            return count

        up = []
        down = []
        # If the Message has already been assigned a Template, we will print that. Otherwise, print the main Fact in
        # the Message.
        if isinstance(this, Message):
            if this.template is not None:
                self.print_tree(this.template, indent=indent, last=last)
            else:
                self.print_tree(this.fact, indent=indent, last=last)
            return
        if isinstance(this, DocumentPlan):
            branch_sizes = {child: rec_count(child) + 1 for child in this.children}

            """ Creation of balanced lists for "up" branch and "down" branch. """
            up = list(this.children)
            while up and sum(branch_sizes[node] for node in down) < sum(branch_sizes[node] for node in up):
                down.insert(0, up.pop())

            """ Printing of "up" branch. """
            for child in up:
                next_last = 'up' if up.index(child) is 0 else ''
                next_indent = '{0}{1}{2}'.format(indent, ' ' if 'up' in last else '│', " " * len(str(this)))
                self.print_tree(child, indent=next_indent, last=next_last)

        """ Printing of current node. """
        if last == 'up':
            start_shape = '┌'
        elif last == 'down':
            start_shape = '└'
        elif last == 'updown':
            start_shape = ' '
        else:
            start_shape = '├'

        if up:
            end_shape = '┤'
        elif down:
            end_shape = '┐'
        else:
            end_shape = ''

        print('{0}{1}{2}{3}'.format(indent, start_shape, str(this), end_shape))

        if isinstance(this, DocumentPlan):
            """ Printing of "down" branch. """
            for child in down:
                next_last = 'down' if down.index(child) is len(down) - 1 else ''
                next_indent = '{0}{1}{2}'.format(indent, ' ' if 'down' in last else '│', " " * len(str(this)))
                self.print_tree(child, indent=next_indent, last=next_last)
