import datetime

from .base_field import BaseField
from ..errors import ConversionError, InvalidTypeError


class DatetimeField(BaseField):
    def __init__(self, value=None, with_hash=False, encrypted=True):
        super().__init__(value, with_hash=with_hash, encrypted=encrypted)

    def _convert_initial_value(self, value):
        if not value:
            return datetime.datetime.fromtimestamp(0)
        elif isinstance(value, datetime.datetime):
            return value
        elif isinstance(value, str):
            try:
                return datetime.datetime.fromisoformat(value)
            except Exception:
                raise ConversionError()
        raise InvalidTypeError()

    def _to_bytes(self, value):
        timestamp = int(value.timestamp())
        return timestamp.to_bytes((timestamp.bit_length() + 7) // 8, "big")

    def _from_bytes(self, value):
        timestamp = int.from_bytes(value, "big")
        return datetime.datetime.fromtimestamp(timestamp)
