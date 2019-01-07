

class ComponentNameCollisionError(Exception):
    pass


class UnknownComponentException(Exception):
    pass


class Registry(object):

    def __init__(self):
        self._registry = {}

    def register(self, name, service):
        if name in self._registry:
            raise ComponentNameCollisionError(
                "A component of name '{}' already exists".format(name))
        else:
            self._registry[name] = service

    def get(self, name):
        if name not in self._registry:
            raise UnknownComponentException(
                "No component named '{}'".format(name))
        else:
            return self._registry[name]
