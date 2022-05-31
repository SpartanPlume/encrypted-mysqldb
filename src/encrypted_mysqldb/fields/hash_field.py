from .base_field import BaseField


class HashField(BaseField):
    def __init__(self, value=None, with_hash=False, encrypted=False):
        super().__init__(value, with_hash=False, encrypted=False)

    def _convert_initial_value(self, value):
        if not value:
            return str()
        return str(value)

    def _to_bytes(self, value):
        return bytes(value, "utf-8")

    def encrypt(self):
        return self.hash()
