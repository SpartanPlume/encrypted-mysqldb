import pytest

from encrypted_mysqldb.fields import IntField
from encrypted_mysqldb.errors import InvalidTypeError, ConversionError


def test_empty():
    """Creates the field without exception and default value 0"""
    int_field = IntField()
    assert int_field.value == 0


def test_convert_initial_value_not_convertible_value():
    """Raises a InvalidTypeError exception when it is not a supported type"""
    # convert_initial_value is implicit in the constructor of the object
    with pytest.raises(InvalidTypeError):
        IntField(["string"])


def test_convert_initial_value_convertible_value_conversion_error():
    """Raises a ConversionError exception when the value could not be converted"""
    # convert_initial_value is implicit in the constructor of the object
    with pytest.raises(ConversionError):
        IntField("string")


def test_convert_initial_value_convertible_value():
    """Returns the value converted to an int"""
    # convert_initial_value is implicit in the constructor of the object
    int_field = IntField("1234")
    assert int_field.value == 1234


def test_convert_initial_value_int_value():
    """Returns the value as is"""
    # convert_initial_value is implicit in the constructor of the object
    value = 1234
    int_field = IntField(value)
    assert int_field.value == value


def test_to_bytes_big_endian():
    """Returns the value converted to bytes"""
    int_field = IntField(1234, endian="big")
    assert int_field._to_bytes(int_field.value) == b"\x04\xd2"


def test_to_bytes_little_endian():
    """Returns the value converted to bytes"""
    int_field = IntField(1234, endian="little")
    assert int_field._to_bytes(int_field.value) == b"\xd2\x04"


def test_to_bytes_unsigned():
    """Returns the value converted to bytes"""
    int_field = IntField(1234, signed=False)
    assert int_field._to_bytes(int_field.value) == b"\x04\xd2"


def test_from_bytes_big_endian():
    """Returns the value converted from bytes to int"""
    int_field = IntField(b"\xfb.", endian="big")
    assert int_field._from_bytes(int_field.value) == -1234


def test_from_bytes_little_endian():
    """Returns the value converted from bytes to int"""
    int_field = IntField(b"\xfb.", endian="little")
    assert int_field._from_bytes(int_field.value) == 12027


def test_from_bytes_unsigned():
    """Returns the value converted from bytes to int"""
    int_field = IntField(b"\xfb.", signed=False)
    assert int_field._from_bytes(int_field.value) == 64302
