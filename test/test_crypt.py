import pytest

from cryptography.fernet import Fernet

from encrypted_mysqldb import crypt
from encrypted_mysqldb.fields import IdField, HashField, IntField, ListField, SetField, StrField
from encrypted_mysqldb.table import Table
from encrypted_mysqldb import init_crypt


@pytest.fixture(autouse=True, scope="module")
def init_tests():
    init_crypt(Fernet("j4SrBByAd-KOhttIcQZ-oO4tsnDo2Wfu4tY9zBb73ZU="))


def test_get_encrypted_obj_fields_no_object():
    """Returns an empty dictionary"""
    assert crypt.get_encrypted_obj_fields(None) == {}


def test_get_encrypted_obj_fields_empty_object():
    """Returns an empty dictionary"""

    class EmptyTable(Table):
        pass

    assert crypt.get_encrypted_obj_fields(EmptyTable()) == {"id": 0}


def test_get_encrypted_obj_fields_object_without_fields():
    """Returns an empty dictionary"""

    class TableWithoutFields(Table):
        a = 1
        b = "2"

    assert crypt.get_encrypted_obj_fields(TableWithoutFields()) == {"id": 0}


def test_get_encrypted_obj_fields_object_with_normal_fields():
    """Returns a dictionary with all attributes and their encrypted value"""

    class TableWithNormalFields(Table):
        id = IdField()
        hash_field = HashField("text")
        int_field = IntField()
        list_field = ListField(IntField, [1, 3, 6])
        set_field = SetField(StrField)
        str_field = StrField()

    table = TableWithNormalFields(int_field=5)
    table.str_field = "abc"
    encrypted_fields = crypt.get_encrypted_obj_fields(table)
    assert encrypted_fields["id"] == 0
    assert (
        encrypted_fields["hash_field"]
        == b"\x00e\x15\x93\r\x84\xf1\xddw\x0e\x9b\xbb:\x96\xd0\xd1\x8d\xbf0\xb1\xe5`/\x0e\x7f\xa8\x1cy\xeb\x94\x12o\x82>\x08*|\xe2\xf6\x8d2\xbe\xecR\xe1'\x088\xc8\xe4\xbf\x0b\x89P)\x15um\xd2\xebI6RF"
    )
    assert type(encrypted_fields["int_field"]) is bytes
    assert type(encrypted_fields["list_field"]) is bytes
    assert type(encrypted_fields["set_field"]) is bytes
    assert type(encrypted_fields["str_field"]) is bytes


def test_get_encrypted_obj_fields_object_with_field_with_hash():
    """Returns a dictionary with encrypted attribute and its hashed value"""

    class TableWithFieldWithHash(Table):
        id = IdField()
        str_field = StrField(with_hash=True)

    table = TableWithFieldWithHash()
    table.str_field = "text"
    encrypted_fields = crypt.get_encrypted_obj_fields(table)
    assert (
        encrypted_fields["str_field_hash"]
        == b"\x00e\x15\x93\r\x84\xf1\xddw\x0e\x9b\xbb:\x96\xd0\xd1\x8d\xbf0\xb1\xe5`/\x0e\x7f\xa8\x1cy\xeb\x94\x12o\x82>\x08*|\xe2\xf6\x8d2\xbe\xecR\xe1'\x088\xc8\xe4\xbf\x0b\x89P)\x15um\xd2\xebI6RF"
    )
    assert type(encrypted_fields["str_field"]) is bytes


def test_get_decrypted_obj_fields_no_fields():
    """Returns an empty dictionary"""
    assert crypt.get_decrypted_obj_fields(None, {}) == {}


def test_get_decrypted_obj_fields_object_without_fields():
    """Returns an empty dictionary"""

    class TableWithoutFields(Table):
        a = 1
        b = "2"

    encrypted_fields = {"a": 1, "b": "2"}
    assert crypt.get_decrypted_obj_fields(TableWithoutFields, encrypted_fields) == {}


def test_get_decrypted_obj_fields_fields_not_in_object():
    """Returns an empty dictionary"""

    class TableWithoutFields(Table):
        str_field = StrField()

    encrypted_fields = {"a": 1, "b": "2"}
    assert crypt.get_decrypted_obj_fields(TableWithoutFields, encrypted_fields) == {}


def test_get_decrypted_obj_fields_object_with_normal_fields():
    """Returns an empty dictionary"""

    class TableWithNormalFields(Table):
        id = IdField()
        hash_field = HashField("text")
        int_field = IntField()
        list_field = ListField(IntField, [1, 3, 6])
        set_field = SetField(StrField)
        str_field = StrField()

    encrypted_fields = {
        "id": 1,
        "hash_field": b"\x00e\x15\x93\r\x84\xf1\xddw\x0e\x9b\xbb:\x96\xd0\xd1\x8d\xbf0\xb1\xe5`/\x0e\x7f\xa8\x1cy\xeb\x94\x12o\x82>\x08*|\xe2\xf6\x8d2\xbe\xecR\xe1'\x088\xc8\xe4\xbf\x0b\x89P)\x15um\xd2\xebI6RF",
        "int_field": b"gAAAAABiJLb5qMjIs5NDgymNbm29nk_UegFAWx13Pj5VK1gJy41FjIcvqyDLnT_KHbtyheU_AU9VEjM8LGEpCaXnTgNkQQrlfA==",
        "list_field": b"gAAAAABiJLb52gPVMv-IDHhX-mI_U9JmD8NKL8DHm44sC14G0RqaLjX_U71FpR8ZALyDHSSi6Jhr191Q8xhxfhDNv2BOQjy3rg==",
        "set_field": b"gAAAAABiJLb5NbLdVrGc5A6hV3lReXO-m-O3j7SCZng48thsy3DsNcwR_QsIPNN55WuARvupUO_pclie2i_6vfR_CXrbCehM3w==",
        "str_field": b"gAAAAABiJLb5cIzaVmZq0H-V-7K_8nUgEnHNUduQjwQ7x_Mm5a5hCrDUHX9SljW4RrNzjXkbptOyw8rlHbpqh0tu2ZYyGFl_fg==",
    }
    decrypted_fields = crypt.get_decrypted_obj_fields(TableWithNormalFields, encrypted_fields)
    assert decrypted_fields["id"] == 1
    assert (
        decrypted_fields["hash_field"]
        == b"\x00e\x15\x93\r\x84\xf1\xddw\x0e\x9b\xbb:\x96\xd0\xd1\x8d\xbf0\xb1\xe5`/\x0e\x7f\xa8\x1cy\xeb\x94\x12o\x82>\x08*|\xe2\xf6\x8d2\xbe\xecR\xe1'\x088\xc8\xe4\xbf\x0b\x89P)\x15um\xd2\xebI6RF"
    )
    assert decrypted_fields["int_field"] == 5
    assert decrypted_fields["list_field"] == [1, 3, 6]
    assert decrypted_fields["set_field"] == set()
    assert decrypted_fields["str_field"] == "abc"
