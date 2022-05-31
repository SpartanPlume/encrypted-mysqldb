import datetime
import pytest

from encrypted_mysqldb.fields import DatetimeField
from encrypted_mysqldb.errors import ConversionError, InvalidTypeError


def test_empty():
    """Creates the field without exception and default value str()"""
    datetime_field = DatetimeField()
    assert datetime_field.value == datetime.datetime(1970, 1, 1, 1, 0)


def test_invalid_value_field_type():
    """Raises a InvalidTypeError exception when it is not a supported type"""
    # convert_initial_value is implicit in the constructor of the object
    with pytest.raises(InvalidTypeError):
        DatetimeField(123)


def test_convert_initial_value_str_isoformat():
    """Converts the isoformat to datetime"""
    # convert_initial_value is implicit in the constructor of the object
    datetime_field = DatetimeField("2019-01-02T12:34:56")
    assert datetime_field.value == datetime.datetime(2019, 1, 2, 12, 34, 56)


def test_convert_initial_value_str_not_isoformat():
    """Raises a InvalidTypeError exception when it is not a supported type"""
    # convert_initial_value is implicit in the constructor of the object
    with pytest.raises(ConversionError):
        DatetimeField("abc")


def test_to_bytes():
    """Returns the value as a bytes value"""
    datetime_field = DatetimeField(datetime.datetime(2020, 1, 2, 3, 4, 5))
    assert datetime_field._to_bytes(datetime_field.value) == b"^\rO\x95"


def test_from_bytes():
    """Returns the value converted from bytes to string"""
    datetime_field = DatetimeField(b"^\rO\x95")
    assert datetime_field._from_bytes(datetime_field.value) == datetime.datetime(2020, 1, 2, 3, 4, 5)
