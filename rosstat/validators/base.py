from collections import namedtuple

Error = namedtuple('Error', ('message', 'code'))


class AbstractValidator:
    def __init__(self, schema):
        self._schema = schema

    def error(self, *args):
        self.errors.append(Error(*args))

    def validate(self, report):
        raise NotImplementedError
