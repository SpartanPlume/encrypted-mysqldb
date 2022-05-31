import pytest

from encrypted_mysqldb.fields import StrField
from encrypted_mysqldb.errors import ConversionError


def test_empty():
    """Creates the field without exception and default value str()"""
    str_field = StrField()
    assert str_field.value == str()


def test_convert_initial_value_convertible_value_conversion_error():
    """Raises a InvalidTypeError exception when it is not a supported type"""
    # convert_initial_value is implicit in the constructor of the object
    class NotConvertibleAsStr:
        def __str__(self):
            raise Exception()

    with pytest.raises(ConversionError):
        StrField(NotConvertibleAsStr())


def test_convert_initial_value():
    """Returns the value as a string"""
    # convert_initial_value is implicit in the constructor of the object
    str_field = StrField(1234)
    assert str_field.value == "1234"


def test_to_bytes():
    """Returns the value as a bytes value"""
    str_field = StrField("string")
    assert str_field._to_bytes(str_field.value) == b"string"


def test_from_bytes():
    """Returns the value converted from bytes to string"""
    str_field = StrField(b"string")
    assert str_field._from_bytes(str_field.value) == "string"
