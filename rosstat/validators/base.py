from collections import namedtuple

Error = namedtuple('Error', ('description', 'code', 'level'))


class AbstractValidator:
    def __init__(self, schema):
        self._schema = schema

    def error(self, *args, level=1):
        self.errors.append(Error(*args, level))

    def validate(self, report):
        raise NotImplementedError
