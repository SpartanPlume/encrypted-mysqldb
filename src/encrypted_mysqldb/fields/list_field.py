from .base_field import BaseField
from ..errors import ConversionError, InvalidTypeError


class ListField(BaseField):
    def __init__(self, value_field_type, value=None, with_hash=False, encrypted=True, separator_in_database="\n"):
        if not issubclass(value_field_type, BaseField):
            raise InvalidTypeError()
        super().__init__(value, with_hash=with_hash, encrypted=encrypted)
        self.value_field_type = value_field_type
        self.separator_in_database = separator_in_database

    def _convert_initial_value(self, value):
        if not value:
            return list()
        elif isinstance(value, list):
            return value
        elif isinstance(value, set):
            return list(value)
        elif not self.encrypted and isinstance(value, str):
            return value
        raise InvalidTypeError()

    def _to_string(self, value):
        list_values = []
        if value:
            try:
                for value_to_modify in value:
                    if not isinstance(value_to_modify, self.value_field_type):
                        # Convert to field to check that values are valid before converting to bytes
                        value_to_modify = self.value_field_type(value_to_modify)
                    list_values.append(str(value_to_modify.value))
            except Exception:
                raise ConversionError()
        return self.separator_in_database.join(list_values)

    def _from_string(self, value):
        if value:
            list_values = value.split(self.separator_in_database)
        else:
            list_values = []
        try:
            new_list_values = [self.value_field_type(list_value).value for list_value in list_values]
        except Exception:
            raise ConversionError()
        return new_list_values

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
        if not isinstance(decrypted_value, list):
            return self._from_string(decrypted_value)
        return decrypted_value
