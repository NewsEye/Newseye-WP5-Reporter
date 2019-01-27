# TODO: Some of these are not necessarily generic. EntitySource and TimeSource are especially suspect

class SlotSource(object):
    """ Source of the slot value """

    def __init__(self, field_name: str) -> None:
        self.field_name = field_name

    def __call__(self, message):
        raise NotImplementedError("abstract slot source")


class FactFieldSource(SlotSource):
    def __init__(self, field_name):
        super().__init__(field_name)

    def __call__(self, message):
        return getattr(message, self.field_name)

    def __str__(self):
        return 'fact.{}'.format(self.field_name)


class LiteralSource(SlotSource):
    """Ignore the message and return a literal value"""
    def __init__(self, value):
        super().__init__('literal')
        self.value = value

    def __call__(self, message):
        return self.value

    def __str__(self):
        return '"{}"'.format(self.value)


class EntitySource(SlotSource):
    """
    Special type of SlotSource for named entities.
    """
    def __init__(self, field_name):
        super().__init__(field_name)

    def __call__(self, message):
        return '[ENTITY:{}:{}]'.format(getattr(message, self.field_name + '_type'), getattr(message, self.field_name))

    def __str__(self):
        return 'fact.{}'.format(self.field_name)


class TimeSource(SlotSource):
    """
    Special type of SlotSource for time entries.
    """
    def __init__(self, field_name):
        super().__init__(field_name)

    def __call__(self, message):
        return '[TIME:{}:{}:{}]'.format(getattr(message, 'when_1'), getattr(message, 'when_2'))

    def __str__(self):
        return 'fact.time'
