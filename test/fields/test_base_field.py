import pytest

from encrypted_mysqldb.fields.base_field import BaseField
from encrypted_mysqldb.errors import NotImplementedError
from encrypted_mysqldb import init_crypt


@pytest.fixture(autouse=True, scope="module")
def init_tests():
    class Crypt:
        def encrypt(self, *args):
            pass

        def decrypt(self, *args):
            pass

    init_crypt(Crypt())


def test_init_do_not_convert_bytes_value():
    """Keeps the bytes value as is"""
    value = b"string"
    base_field = BaseField(value)
    assert base_field.value == value


def test_convert_initial_value():
    """Returns the value as is"""
    # convert_initial_value is implicit in the constructor of the object
    value = "string"
    base_field = BaseField(value)
    assert base_field.value == value


def test_eq_with_equal_base_field_value():
    """Compares value in both fields and returns True"""
    assert BaseField("abc", with_hash=False, encrypted=True) == BaseField("abc", with_hash=True, encrypted=False)


def test_not_eq_with_different_base_field_value():
    """Compares value in both fields and returns False"""
    assert BaseField("abc") != BaseField("def")


def test_eq_with_non_field_equivalent_value():
    """Compares value in field with non field value and returns True"""
    assert BaseField("abc") == "abc"


def test_not_eq_with_non_field_different_value():
    """Compares value in field with non field value and returns False"""
    assert BaseField("abc") != "def"


def test_to_bytes():
    """Raises a NotImplementedError exception"""
    base_field = BaseField()
    with pytest.raises(NotImplementedError):
        base_field._to_bytes(base_field.value)


def test_from_bytes():
    """Raises a NotImplementedError exception"""
    base_field = BaseField()
    with pytest.raises(NotImplementedError):
        base_field._from_bytes(base_field.value)


def test_hash_no_value():
    """Returns None when the value is None"""
    base_field = BaseField(None)
    assert base_field.hash() is None


def test_hash_bytes_value():
    """Returns the value as is"""
    value = b"string"
    base_field = BaseField(value)
    assert base_field.hash() == value


def test_hash_not_bytes_value():
    """Raises a NotImplementedError exception since _to_bytes is not implemented"""
    base_field = BaseField("string")
    with pytest.raises(NotImplementedError):
        base_field.hash()


def test_encrypt_bytes_value():
    """Returns the value as is"""
    value = b"string"
    base_field = BaseField(value)
    assert base_field.encrypt() == value


def test_encrypt_field_not_encrypted():
    """Returns the value as is"""
    value = "string"
    base_field = BaseField(value, encrypted=False)
    assert base_field.encrypt() == value


def test_encrypt_not_bytes_value():
    """Raises a NotImplementedError exception since _to_bytes is not implemented"""
    base_field = BaseField("string")
    with pytest.raises(NotImplementedError):
        base_field.encrypt()


def test_decrypt_bytes_value():
    """Raises a NotImplementedError exception since _from_bytes is not implemented"""
    base_field = BaseField(b"string")
    with pytest.raises(NotImplementedError):
        base_field.decrypt()


def test_decrypt_field_not_encrypted():
    """Returns the value as is"""
    value = "string"
    base_field = BaseField(value, encrypted=False)
    assert base_field.decrypt() == value


def test_decrypt_not_bytes_value():
    """Returns the value as is"""
    value = "string"
    base_field = BaseField(value)
    assert base_field.decrypt() == value
