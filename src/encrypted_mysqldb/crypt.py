import copy

from .fields.base_field import BaseField
from .table import get_real_table_attribute


def get_encrypted_obj_fields(obj):
    if not obj:
        return {}
    obj_fields = vars(obj)
    encrypted_fields = {}
    for key, value in obj_fields.items():
        try:
            class_value = get_real_table_attribute(type(obj), key)
        except Exception:
            continue
        if not isinstance(class_value, BaseField):
            continue
        if isinstance(value, BaseField):
            field_to_encrypt = value
        else:
            field_to_encrypt = copy.deepcopy(class_value)
            field_to_encrypt.value = value
        encrypted_fields[key] = field_to_encrypt.encrypt()
        if field_to_encrypt.with_hash:
            encrypted_fields[key + "_hash"] = field_to_encrypt.hash()
    return encrypted_fields


def get_decrypted_obj_fields(obj_class, fields):
    decrypted_fields = {}
    for key, value in fields.items():
        try:
            class_value = get_real_table_attribute(obj_class, key)
        except Exception:
            continue
        if not isinstance(class_value, BaseField):
            continue
        field_to_decrypt = copy.deepcopy(class_value)
        field_to_decrypt.value = value
        decrypted_fields[key] = field_to_decrypt.decrypt()
    return decrypted_fields
