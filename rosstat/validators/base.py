from collections import namedtuple

Error = namedtuple("Error", ("description", "code", "level"))


class AbstractValidator:
    def error(self, description, code, level=1):
        self.errors.append(Error(description, code, level))

    def validate(self, report):
        raise NotImplementedError
