import pytest

from encrypted_mysqldb.fields import SetField, StrField, IntField
from encrypted_mysqldb.errors import InvalidTypeError, ConversionError


def test_empty():
    """Creates the field without exception and default value set()"""
    set_field = SetField(StrField)
    assert set_field.value == set()


def test_invalid_value_field_type():
    """Raises a InvalidTypeError exception when it is not a supported type"""
    # convert_initial_value is implicit in the constructor of the object
    with pytest.raises(InvalidTypeError):
        SetField(str, "string")


def test_convert_initial_value_not_convertible_value():
    """Raises a InvalidTypeError exception when it is not a supported type"""
    # convert_initial_value is implicit in the constructor of the object
    with pytest.raises(InvalidTypeError):
        SetField(StrField, "string")


def test_convert_initial_value_convertible_value():
    """Returns the value converted to a set"""
    # convert_initial_value is implicit in the constructor of the object
    set_field = SetField(StrField, ["string"])
    assert set_field.value == {"string"}


def test_convert_initial_value_set_value():
    """Returns the value as is"""
    # convert_initial_value is implicit in the constructor of the object
    value = {1234}
    set_field = SetField(IntField, value)
    assert set_field.value == value


def test_to_bytes():
    """Returns the value converted to bytes"""
    set_field = SetField(IntField, {1, 2, 3, 4})
    assert sorted(set_field._to_bytes(set_field.value)) == sorted(b"1\n2\n3\n4")


def test_to_bytes_with_implicit_conversion():
    """Returns the value converted to bytes"""
    set_field = SetField(IntField, {1, IntField(2), IntField("3"), "4"})
    assert sorted(set_field._to_bytes(set_field.value)) == sorted(b"1\n2\n3\n4")


def test_to_bytes_with_different_separator():
    """Returns the value converted to bytes, with a different separator between elements"""
    set_field = SetField(IntField, {1, 2, 3, 4}, separator_in_database=",")
    assert sorted(set_field._to_bytes(set_field.value)) == sorted(b"1,2,3,4")


def test_to_bytes_conversion_error():
    """Raises a InvalidTypeError exception when the set contains an unsupported type"""
    set_field = SetField(IntField, {"a", "b", "c", "d"})
    with pytest.raises(ConversionError):
        assert set_field._to_bytes(set_field.value)


def test_from_bytes():
    """Returns the value converted from bytes to set"""
    set_field = SetField(IntField, b"1\n2\n3\n4")
    assert set_field._from_bytes(set_field.value) == {1, 2, 3, 4}


def test_from_bytes_empty():
    """Returns an empty set"""
    set_field = SetField(IntField, b"")
    assert set_field._from_bytes(set_field.value) == set()


def test_from_bytes_with_different_separator():
    """Returns the value converted from bytes to set, with a different separator between elements"""
    set_field = SetField(StrField, b"1,2,3,4", separator_in_database=",")
    assert set_field._from_bytes(set_field.value) == {"1", "2", "3", "4"}


def test_from_bytes_conversion_error():
    """Raises a InvalidTypeError exception when the set contains an unsupported type"""
    set_field = SetField(IntField, b"a,b,c,d")
    with pytest.raises(ConversionError):
        assert set_field._from_bytes(set_field.value)


def test_encrypt_when_not_encrypted():
    """Returns a concatenated string"""
    set_field = SetField(IntField, {1, 2, 3, 4}, encrypted=False)
    assert sorted(set_field.encrypt()) == sorted("1\n2\n3\n4")


def test_encrypt_when_not_encrypted_empty_list():
    """Returns an empty string"""
    set_field = SetField(IntField, set(), encrypted=False)
    assert set_field.encrypt() == ""


def test_decrypt_when_not_encrypted():
    """Returns a set from the concatenated string"""
    set_field = SetField(IntField, "1\n2\n3\n4", encrypted=False)
    assert set_field.decrypt() == {1, 2, 3, 4}
