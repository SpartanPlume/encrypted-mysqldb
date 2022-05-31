import hashlib

from encrypted_mysqldb.fields import HashField


def test_empty():
    """Creates the field without exception and default value str()"""
    hash_field = HashField()
    assert hash_field.value == str()


def test_convert_initial_value():
    """Returns the value as a string"""
    # convert_initial_value is implicit in the constructor of the object
    hash_field = HashField(1234)
    assert hash_field.value == "1234"


def test_to_bytes():
    """Returns the value as a bytes value"""
    hash_field = HashField("string")
    assert hash_field._to_bytes(hash_field.value) == b"string"


def test_encrypt():
    """Returns the value as a hashed string"""
    hash_field = HashField("string")
    hashed_value = hashlib.blake2b(b"string").digest()
    assert hash_field.encrypt() == hashed_value
