from .base_field import BaseField
from ..errors import InvalidTypeError, ConversionError


class BoolField(BaseField):
    def __init__(self, value=None, with_hash=False, encrypted=True):
        super().__init__(value, with_hash=with_hash, encrypted=encrypted)

    def _convert_initial_value(self, value):
        if not value:
            return False
        elif isinstance(value, bool):
            return value
        elif isinstance(value, (float, int)):
            try:
                return bool(value)
            except Exception:
                raise ConversionError()
        raise InvalidTypeError()

    def _to_bytes(self, value):
        int_value = int(value)
        return int_value.to_bytes((int_value.bit_length() + 7) // 8, "big")

    def _from_bytes(self, value):
        int_value = int.from_bytes(value, "big")
        return bool(int_value)
