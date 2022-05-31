import pytest

from encrypted_mysqldb.fields import ListField, StrField, IntField
from encrypted_mysqldb.errors import InvalidTypeError, ConversionError


def test_empty():
    """Creates the field without exception and default value list()"""
    list_field = ListField(StrField)
    assert list_field.value == list()


def test_invalid_value_field_type():
    """Raises a InvalidTypeError exception when it is not a supported type"""
    # convert_initial_value is implicit in the constructor of the object
    with pytest.raises(InvalidTypeError):
        ListField(str, "string")


def test_convert_initial_value_not_convertible_value():
    """Raises a InvalidTypeError exception when it is not a supported type"""
    # convert_initial_value is implicit in the constructor of the object
    with pytest.raises(InvalidTypeError):
        ListField(StrField, "string")


def test_convert_initial_value_convertible_value():
    """Returns the value converted to a list"""
    # convert_initial_value is implicit in the constructor of the object
    list_field = ListField(StrField, {"string"})
    assert list_field.value == ["string"]


def test_convert_initial_value_list_value():
    """Returns the value as is"""
    # convert_initial_value is implicit in the constructor of the object
    value = [1234]
    list_field = ListField(IntField, value)
    assert list_field.value == value


def test_to_bytes():
    """Returns the value converted to bytes"""
    list_field = ListField(IntField, [1, 2, 3, 4])
    assert list_field._to_bytes(list_field.value) == b"1\n2\n3\n4"


def test_to_bytes_with_implicit_conversion():
    """Returns the value converted to bytes"""
    list_field = ListField(IntField, [1, IntField(2), IntField("3"), "4"])
    assert list_field._to_bytes(list_field.value) == b"1\n2\n3\n4"


def test_to_bytes_with_different_separator():
    """Returns the value converted to bytes, with a different separator between elements"""
    list_field = ListField(IntField, [1, 2, 3, 4], separator_in_database=",")
    assert list_field._to_bytes(list_field.value) == b"1,2,3,4"


def test_to_bytes_conversion_error():
    """Raises a InvalidTypeError exception when the list contains an unsupported type"""
    list_field = ListField(IntField, ["a", "b", "c", "d"])
    with pytest.raises(ConversionError):
        assert list_field._to_bytes(list_field.value)


def test_from_bytes():
    """Returns the value converted from bytes to list"""
    list_field = ListField(IntField, b"1\n2\n3\n4")
    assert list_field._from_bytes(list_field.value) == [1, 2, 3, 4]


def test_from_bytes_empty():
    """Returns an empty list"""
    list_field = ListField(IntField, b"")
    assert list_field._from_bytes(list_field.value) == []


def test_from_bytes_with_different_separator():
    """Returns the value converted from bytes to list, with a different separator between elements"""
    list_field = ListField(StrField, b"1,2,3,4", separator_in_database=",")
    assert list_field._from_bytes(list_field.value) == ["1", "2", "3", "4"]


def test_from_bytes_conversion_error():
    """Raises a InvalidTypeError exception when the list contains an unsupported type"""
    list_field = ListField(IntField, b"a,b,c,d")
    with pytest.raises(ConversionError):
        assert list_field._from_bytes(list_field.value)


def test_encrypt_when_not_encrypted():
    """Returns a concatenated string"""
    list_field = ListField(IntField, [1, 2, 3, 4], encrypted=False)
    assert list_field.encrypt() == "1\n2\n3\n4"


def test_encrypt_when_not_encrypted_empty_list():
    """Returns an empty string"""
    list_field = ListField(IntField, [], encrypted=False)
    assert list_field.encrypt() == ""


def test_decrypt_when_not_encrypted():
    """Returns a list from the concatenated string"""
    list_field = ListField(IntField, "1\n2\n3\n4", encrypted=False)
    assert list_field.decrypt() == [1, 2, 3, 4]
