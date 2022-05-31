from .base_field import BaseField
from ..errors import ConversionError


class StrField(BaseField):
    def __init__(self, value=None, with_hash=False, encrypted=True):
        super().__init__(value, with_hash=with_hash, encrypted=encrypted)

    def _convert_initial_value(self, value):
        if not value:
            return str()
        elif isinstance(value, str):
            return value
        try:
            return str(value)
        except Exception:
            raise ConversionError()

    def _to_bytes(self, value):
        return bytes(value, "utf-8")

    def _from_bytes(self, value):
        return value.decode("utf-8")
