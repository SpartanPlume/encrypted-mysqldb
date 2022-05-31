from .base_field import BaseField
from ..errors import InvalidTypeError, ConversionError


class SetField(BaseField):
    def __init__(self, value_field_type, value=None, with_hash=False, encrypted=True, separator_in_database="\n"):
        if not issubclass(value_field_type, BaseField):
            raise InvalidTypeError()
        super().__init__(value, with_hash=with_hash, encrypted=encrypted)
        self.value_field_type = value_field_type
        self.separator_in_database = separator_in_database

    def _convert_initial_value(self, value):
        if not value:
            return set()
        elif isinstance(value, set):
            return value
        elif isinstance(value, list):
            return set(value)
        elif not self.encrypted and isinstance(value, str):
            return value
        raise InvalidTypeError()

    def _to_string(self, value):
        set_values = set()
        try:
            for value_to_modify in value:
                if not isinstance(value_to_modify, self.value_field_type):
                    # Convert to field to check that values are valid before converting to bytes
                    value_to_modify = self.value_field_type(value_to_modify)
                set_values.add(str(value_to_modify.value))
        except Exception:
            raise ConversionError()
        return self.separator_in_database.join(set_values)

    def _from_string(self, value):
        if value:
            set_values = value.split(self.separator_in_database)
        else:
            set_values = []
        try:
            new_set_values = set([self.value_field_type(set_value).value for set_value in set_values])
        except Exception:
            raise ConversionError()
        return new_set_values

    def _to_bytes(self, value):
        return bytes(self._to_string(value), "utf-8")

    def _from_bytes(self, value):
        return self._from_string(value.decode("utf-8"))

    def encrypt(self):
        encrypted_value = super().encrypt()
        if not isinstance(encrypted_value, bytes):
            return self._to_string(encrypted_value)
        return encrypted_value

    def decrypt(self):
        decrypted_value = super().decrypt()
        if not isinstance(decrypted_value, set):
            return self._from_string(decrypted_value)
        return decrypted_value
