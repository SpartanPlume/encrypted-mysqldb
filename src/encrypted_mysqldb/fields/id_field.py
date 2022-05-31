from .base_field import BaseField
from ..errors import NotImplementedError, InvalidTypeError


class IdField(BaseField):
    def __init__(self, value=None, with_hash=False, encrypted=False):
        super().__init__(value, with_hash=False, encrypted=False)

    def _convert_initial_value(self, value):
        if not value:
            value = 0
        elif not isinstance(value, int):
            raise InvalidTypeError()
        return value

    def hash(self):
        raise NotImplementedError()

    def encrypt(self):
        return self.value

    def decrypt(self):
        return self.value
