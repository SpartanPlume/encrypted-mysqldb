import hashlib

from ..errors import NotImplementedError
from .. import get_crypt


class BaseField:
    def __init__(self, value=None, with_hash=False, encrypted=True):
        self.with_hash = with_hash
        self.encrypted = encrypted
        self.value = value

    def __setattr__(self, __name, __value):
        if __name == "value":
            if not isinstance(__value, bytes):
                super().__setattr__(__name, self._convert_initial_value(__value))
                return
        super().__setattr__(__name, __value)

    def __eq__(self, __o):
        if isinstance(__o, BaseField):
            return self.value == __o.value
        return self.value == __o

    def __hash__(self):
        return hash(self.value)

    def _convert_initial_value(self, value):
        return value

    def _to_bytes(self, value):
        raise NotImplementedError()

    def _from_bytes(self, value):
        raise NotImplementedError()

    def hash(self):
        if not self.value:
            return None
        if isinstance(self.value, bytes):
            return self.value
        return hashlib.blake2b(self._to_bytes(self.value)).digest()

    def encrypt(self):
        if isinstance(self.value, bytes) or not self.encrypted:
            return self.value
        return get_crypt().encrypt(self._to_bytes(self.value))

    def decrypt(self):
        if not isinstance(self.value, bytes) or not self.encrypted:
            return self.value
        return self._from_bytes(get_crypt().decrypt(self.value))
