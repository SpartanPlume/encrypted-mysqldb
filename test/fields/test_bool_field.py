import pytest

from encrypted_mysqldb.fields import BoolField
from encrypted_mysqldb.errors import InvalidTypeError


def test_empty():
    """Creates the field without exception and default value str()"""
    bool_field = BoolField()
    assert bool_field.value is False


def test_invalid_value_field_type():
    """Raises a InvalidTypeError exception when it is not a supported type"""
    # convert_initial_value is implicit in the constructor of the object
    with pytest.raises(InvalidTypeError):
        BoolField("abc")


def test_convert_initial_value():
    """Converts int value to bool"""
    # convert_initial_value is implicit in the constructor of the object
    bool_field = BoolField(123)
    assert bool_field.value is True


def test_to_bytes():
    """Returns the value as a bytes value"""
    bool_field = BoolField(True)
    assert bool_field._to_bytes(bool_field.value) == b"\x01"


def test_from_bytes():
    """Returns the value converted from bytes to string"""
    bool_field = BoolField(b"\x01")
    assert bool_field._from_bytes(bool_field.value) is True
