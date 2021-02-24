from collections import namedtuple

Error = namedtuple('Error', ('message', 'code', 'tip'))


class AbstractValidator:
    def __init__(self, schema):
        self._schema = schema

    def error(self, *args, tip=True):
        self.errors.append(Error(*args, tip))

    def validate(self, report):
        raise NotImplementedError
