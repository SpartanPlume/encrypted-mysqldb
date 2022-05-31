from .base_field import BaseField
from ..errors import ConversionError, InvalidTypeError


class IntField(BaseField):
    def __init__(self, value=None, with_hash=False, encrypted=True, endian="big", signed=True):
        super().__init__(value, with_hash=with_hash, encrypted=encrypted)
        self.endian = endian
        self.signed = signed

    def _convert_initial_value(self, value):
        if not value:
            return 0
        elif isinstance(value, int):
            return value
        elif isinstance(value, (float, str, bool)):
            try:
                return int(value)
            except Exception:
                raise ConversionError()
        raise InvalidTypeError()

    def _to_bytes(self, value):
        return value.to_bytes((value.bit_length() + 7) // 8, self.endian, signed=self.signed)

    def _from_bytes(self, value):
        return int.from_bytes(value, self.endian, signed=self.signed)
