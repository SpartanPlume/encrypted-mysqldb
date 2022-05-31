import pytest

from encrypted_mysqldb.fields import IdField
from encrypted_mysqldb.errors import InvalidTypeError, NotImplementedError


def test_empty():
    """Creates the field without exception and default value 0"""
    id_field = IdField()
    assert id_field.value == 0


def test_convert_initial_value_not_int_value():
    """Raises a InvalidTypeError exception since only int is supported as an Id"""
    # convert_initial_value is implicit in the constructor of the object
    with pytest.raises(InvalidTypeError):
        IdField("string")


def test_convert_initial_value_int_value():
    """Returns the value as is"""
    # convert_initial_value is implicit in the constructor of the object
    value = 1234
    id_field = IdField(value)
    assert id_field.value == value


def test_hash():
    """Raises a NotImplementedError exception since an Id cannot be hashed"""
    id_field = IdField(1234)
    with pytest.raises(NotImplementedError):
        id_field.hash()


def test_encrypt():
    """Returns the value as is"""
    value = 1234
    id_field = IdField(value)
    assert id_field.encrypt() == value


def test_decrypt():
    """Returns the value as is"""
    value = 1234
    id_field = IdField(value)
    assert id_field.decrypt() == value
