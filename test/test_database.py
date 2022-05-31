import datetime
import subprocess
import pytest

from encrypted_mysqldb.database import Query, Database
from encrypted_mysqldb.errors import (
    DatabaseInitializationError,
    InvalidCryptError,
    NotTableTypeError,
    SearchOnEncryptedFieldError,
)
from encrypted_mysqldb.table import Table
from encrypted_mysqldb.fields import HashField, StrField, ListField, IntField, DatetimeField, BoolField


class Crypt:
    def encrypt(self, *args):
        pass

    def decrypt(self, *args):
        pass


@pytest.fixture(autouse=True, scope="function")
def clean_database():
    subprocess.run(
        [
            """sudo mysql <<EOF
DROP DATABASE IF EXISTS encrypted_mysqldb_test;
CREATE DATABASE IF NOT EXISTS encrypted_mysqldb_test;
GRANT ALL PRIVILEGES ON encrypted_mysqldb_test.* TO 'encrypted_mysqldb_user'@'localhost';
FLUSH PRIVILEGES;
EOF""",
        ],
        shell=True,
    )


@pytest.fixture(autouse=True, scope="function")
def init_tests():
    import gc

    gc.collect()


def test_database():
    """Creates a Database object"""
    Database("encrypted_mysqldb_user", "encrypted_mysqldb_password", "encrypted_mysqldb_test", Crypt())


def test_invalid_crypt():
    """Raises a InvalidCryptError since the crypt object is invalid"""

    class NotCrypt:
        pass

    with pytest.raises(InvalidCryptError):
        Database("encrypted_mysqldb_user", "encrypted_mysqldb_password", "invalid_database", NotCrypt())


def test_invalid_database():
    """Raises a DatabaseInitializationError since the database does not exist"""
    with pytest.raises(DatabaseInitializationError):
        Database("encrypted_mysqldb_user", "encrypted_mysqldb_password", "invalid_database", Crypt())


def test_create_table():
    """Creates a table in a database"""

    class TestTable(Table):
        bool_field = BoolField(encrypted=False)
        hash_field = HashField()
        int_field = IntField(encrypted=False)
        list_field = ListField(StrField)
        str_field = StrField(encrypted=False)
        str_field_with_hash = StrField(with_hash=True)

    database = Database("encrypted_mysqldb_user", "encrypted_mysqldb_password", "encrypted_mysqldb_test", Crypt())
    with database.connection_pool.create_cursor() as cursor:
        cursor.execute("DESC test_table")
        column_names = set([column[0] for column in cursor.fetchall()])
    assert column_names == set(
        [
            "id",
            "bool_field",
            "hash_field",
            "int_field",
            "list_field",
            "str_field",
            "str_field_with_hash",
            "str_field_with_hash_hash",
        ]
    )


def test_create_two_tables():
    """Creates two tables in a database"""

    class TestTable1(Table):
        pass

    class TestTable2(Table):
        pass

    database = Database("encrypted_mysqldb_user", "encrypted_mysqldb_password", "encrypted_mysqldb_test", Crypt())
    with database.connection_pool.create_cursor() as cursor:
        cursor.execute("SHOW TABLES")
        table_names = set([table[0] for table in cursor.fetchall()])
    assert table_names == set(
        [
            "test_table1",
            "test_table2",
        ]
    )


def test_create_subtable():
    """Creates a subtable in a database"""

    class TestTable(Table):
        hash_field = HashField()

    class TestSubtable(TestTable):
        str_field = StrField()

    database = Database("encrypted_mysqldb_user", "encrypted_mysqldb_password", "encrypted_mysqldb_test", Crypt())
    with database.connection_pool.create_cursor() as cursor:
        cursor.execute("DESC test_subtable")
        column_names = set([column[0] for column in cursor.fetchall()])
    assert column_names == set(
        [
            "id",
            "hash_field",
            "str_field",
        ]
    )


def test_create_table_on_already_existing_table_update_table(mocker):
    """Updates a table that already exists in a database"""

    class TestTable(Table):
        pass

    database = Database("encrypted_mysqldb_user", "encrypted_mysqldb_password", "encrypted_mysqldb_test", Crypt())
    database._update_table = mocker.Mock()
    database._create_table(TestTable)
    database._update_table.assert_called_once_with(TestTable)


def test_update_table_add_fields():
    """Updates a table schema by adding columns in a database"""

    class TestTable(Table):
        pass

    database = Database("encrypted_mysqldb_user", "encrypted_mysqldb_password", "encrypted_mysqldb_test", Crypt())

    class TestTable(Table):  # noqa
        hash_field = HashField()
        int_field = IntField(encrypted=False)
        list_field = ListField(StrField)
        str_field = StrField(encrypted=False)
        str_field_with_hash = StrField(with_hash=True)

    database._update_table(TestTable)
    with database.connection_pool.create_cursor() as cursor:
        cursor.execute("DESC test_table")
        column_names = set([column[0] for column in cursor.fetchall()])
    assert column_names == set(
        [
            "id",
            "hash_field",
            "int_field",
            "list_field",
            "str_field",
            "str_field_with_hash",
            "str_field_with_hash_hash",
        ]
    )


def test_update_table_delete_fields():
    """Updates a table schema by deleting columns in a database"""

    class TestTable(Table):
        hash_field = HashField()
        int_field = IntField(encrypted=False)
        list_field = ListField(StrField)
        str_field = StrField(encrypted=False)
        str_field_with_hash = StrField(with_hash=True)

    database = Database("encrypted_mysqldb_user", "encrypted_mysqldb_password", "encrypted_mysqldb_test", Crypt())

    class TestTable(Table):  # noqa
        pass

    database._update_table(TestTable)
    with database.connection_pool.create_cursor() as cursor:
        cursor.execute("DESC test_table")
        column_names = set([column[0] for column in cursor.fetchall()])
    assert column_names == set(["id"])


def test_add_not_table():
    """Raises a NotTableTypeError exception since the parameter is not a Table object"""
    database = Database("encrypted_mysqldb_user", "encrypted_mysqldb_password", "encrypted_mysqldb_test", Crypt())
    with pytest.raises(NotTableTypeError):
        database.add(1)


def test_add_with_only_id(mocker):
    """Adds an object with only an id field in the database"""
    mocker.patch(
        "encrypted_mysqldb.crypt.get_encrypted_obj_fields", mocker.Mock(side_effect=(lambda x: x.get_table_dict()))
    )

    class TestTable(Table):
        pass

    database = Database("encrypted_mysqldb_user", "encrypted_mysqldb_password", "encrypted_mysqldb_test", Crypt())
    added_obj = database.add(TestTable())
    assert added_obj.id == 1
    with database.connection_pool.create_cursor() as cursor:
        cursor.execute("SELECT * FROM " + TestTable.__tablename__)
        results = list(cursor.fetchall())
    assert results == [(1,)]


def test_add():
    """Adds an object in the database"""

    class TestTable(Table):
        int_field = IntField(encrypted=False)
        list_field = ListField(StrField, encrypted=False)
        str_field = StrField(encrypted=False)

    database = Database("encrypted_mysqldb_user", "encrypted_mysqldb_password", "encrypted_mysqldb_test", Crypt())
    database.add(TestTable(int_field=123, list_field=["a", "b", "c"], str_field="text"))
    with database.connection_pool.create_cursor() as cursor:
        cursor.execute("SELECT * FROM " + TestTable.__tablename__)
        results = list(cursor.fetchall())
    assert results == [
        (
            1,
            123,
            "a\nb\nc",
            "text",
        )
    ]


def test_add_with_created_at_and_updated_at(mocker):
    """Adds an object in the database and automatically fills created_at and updated_at fields"""
    mock_datetime = mocker.patch("encrypted_mysqldb.database.datetime")
    mock_datetime.datetime.utcnow.return_value = datetime.datetime(2020, 1, 2, 3, 4, 5)

    class TestTable(Table):
        created_at = DatetimeField(encrypted=False)
        updated_at = DatetimeField(encrypted=False)

    database = Database("encrypted_mysqldb_user", "encrypted_mysqldb_password", "encrypted_mysqldb_test", Crypt())
    database.add(TestTable())
    with database.connection_pool.create_cursor() as cursor:
        cursor.execute("SELECT * FROM " + TestTable.__tablename__)
        results = list(cursor.fetchall())
    assert results == [(1, datetime.datetime(2020, 1, 2, 3, 4, 5), datetime.datetime(2020, 1, 2, 3, 4, 5))]


def test_update_not_table():
    """Raises a NotTableTypeError exception since the parameter is not a Table object"""
    database = Database("encrypted_mysqldb_user", "encrypted_mysqldb_password", "encrypted_mysqldb_test", Crypt())
    with pytest.raises(NotTableTypeError):
        database.update(1)


def test_update():
    """Updates an object in the database"""

    class TestTable(Table):
        int_field = IntField(encrypted=False)
        list_field = ListField(StrField, encrypted=False)
        str_field = StrField(encrypted=False)

    database = Database("encrypted_mysqldb_user", "encrypted_mysqldb_password", "encrypted_mysqldb_test", Crypt())
    with database.connection_pool.create_cursor() as cursor:
        cursor.execute(
            "INSERT INTO {0} ({1}) VALUES (%s, %s, %s)".format(
                TestTable.__tablename__, "int_field, list_field, str_field"
            ),
            [123, "a\nb\nc", "text"],
        )
    database.update(TestTable(id=1, list_field=[1, 2, 3], str_field="new text"))
    with database.connection_pool.create_cursor() as cursor:
        cursor.execute("SELECT * FROM " + TestTable.__tablename__)
        results = list(cursor.fetchall())
    assert results == [
        (
            1,
            0,
            "1\n2\n3",
            "new text",
        )
    ]


def test_update_with_updated_at(mocker):
    """Updates an object in the database and automatically updated the updated_at field"""
    mock_datetime = mocker.patch("encrypted_mysqldb.database.datetime")
    mock_datetime.datetime.utcnow.return_value = datetime.datetime(2021, 2, 3, 4, 5, 6)

    class TestTable(Table):
        updated_at = DatetimeField(encrypted=False)

    database = Database("encrypted_mysqldb_user", "encrypted_mysqldb_password", "encrypted_mysqldb_test", Crypt())
    with database.connection_pool.create_cursor() as cursor:
        cursor.execute(
            "INSERT INTO {0} ({1}) VALUES (%s)".format(TestTable.__tablename__, "updated_at"),
            [datetime.datetime(2020, 1, 2, 3, 4, 5)],
        )
    database.update(TestTable(id=1))
    with database.connection_pool.create_cursor() as cursor:
        cursor.execute("SELECT * FROM " + TestTable.__tablename__)
        results = list(cursor.fetchall())
    assert results == [(1, datetime.datetime(2021, 2, 3, 4, 5, 6))]


def test_update_with_id_not_set(mocker):
    """Does nothing if object does not have a valid id"""
    mocker.patch(
        "encrypted_mysqldb.crypt.get_encrypted_obj_fields", mocker.Mock(side_effect=(lambda x: x.get_table_dict()))
    )

    class TestTable(Table):
        str_field = StrField(encrypted=False)

    database = Database("encrypted_mysqldb_user", "encrypted_mysqldb_password", "encrypted_mysqldb_test", Crypt())
    with database.connection_pool.create_cursor() as cursor:
        cursor.execute("INSERT INTO {0} ({1}) VALUES (%s)".format(TestTable.__tablename__, "str_field"), ["text"])
    database.update(TestTable(id=0, str_field="new text"))
    with database.connection_pool.create_cursor() as cursor:
        cursor.execute("SELECT * FROM " + TestTable.__tablename__)
        results = list(cursor.fetchall())
    assert results == [
        (
            1,
            "text",
        )
    ]


def test_delete_not_table():
    """Raises a NotTableTypeError exception since the parameter is not a Table object"""
    database = Database("encrypted_mysqldb_user", "encrypted_mysqldb_password", "encrypted_mysqldb_test", Crypt())
    with pytest.raises(NotTableTypeError):
        database.delete(1)


def test_delete():
    """Deletes an object in the database"""

    class TestTable(Table):
        int_field = IntField(encrypted=False)
        list_field = ListField(StrField, encrypted=False)
        str_field = StrField(encrypted=False)

    database = Database("encrypted_mysqldb_user", "encrypted_mysqldb_password", "encrypted_mysqldb_test", Crypt())
    with database.connection_pool.create_cursor() as cursor:
        cursor.execute(
            "INSERT INTO {0} ({1}) VALUES (%s, %s, %s)".format(
                TestTable.__tablename__, "int_field, list_field, str_field"
            ),
            [123, "a\nb\nc", "text"],
        )
    database.delete(TestTable(id=1, list_field=[1, 2, 3], str_field="new text"))
    with database.connection_pool.create_cursor() as cursor:
        cursor.execute("SELECT * FROM " + TestTable.__tablename__)
        results = list(cursor.fetchall())
    assert results == []


def test_query_not_table():
    """Raises a NotTableTypeError exception since the parameter is not a Table object"""
    database = Database("encrypted_mysqldb_user", "encrypted_mysqldb_password", "encrypted_mysqldb_test", Crypt())
    with pytest.raises(NotTableTypeError):
        database.query(1)


def test_query():
    """Gets a Query object linked to a table"""

    class TestTable(Table):
        pass

    database = Database("encrypted_mysqldb_user", "encrypted_mysqldb_password", "encrypted_mysqldb_test", Crypt())
    query = database.query(TestTable)
    assert query.database == database
    assert query.obj_class == TestTable
    assert query.query == "SELECT * FROM test_table"


def test_query_where_empty_value():
    """Fills the query string in the Query object with a NULL param"""

    class TestTable(Table):
        str_field = StrField(encrypted=False)

    database = Database("encrypted_mysqldb_user", "encrypted_mysqldb_password", "encrypted_mysqldb_test", Crypt())
    query = Query(database, TestTable)
    query.where(TestTable.str_field == None)  # noqa
    assert query.query == "SELECT * FROM test_table WHERE str_field = %s"
    assert query.params == ["NULL"]


def test_query_where_on_field_with_hash():
    """Fills the query string in the Query object with a search on a field with hash"""

    class TestTable(Table):
        str_field = StrField(with_hash=True)

    database = Database("encrypted_mysqldb_user", "encrypted_mysqldb_password", "encrypted_mysqldb_test", Crypt())
    query = Query(database, TestTable)
    query.where(TestTable.str_field == "text")
    assert query.query == "SELECT * FROM test_table WHERE str_field_hash = %s"
    assert query.params == [
        b"\x00e\x15\x93\r\x84\xf1\xddw\x0e\x9b\xbb:\x96\xd0\xd1\x8d\xbf0\xb1\xe5`/\x0e\x7f\xa8\x1cy\xeb\x94\x12o\x82>\x08*|\xe2\xf6\x8d2\xbe\xecR\xe1'\x088\xc8\xe4\xbf\x0b\x89P)\x15um\xd2\xebI6RF"
    ]


def test_query_where_hash_field():
    """Fills the query string in the Query object with a search on a HashField"""

    class TestTable(Table):
        hash_field = HashField()

    database = Database("encrypted_mysqldb_user", "encrypted_mysqldb_password", "encrypted_mysqldb_test", Crypt())
    query = Query(database, TestTable)
    query.where(TestTable.hash_field == "text")
    assert query.query == "SELECT * FROM test_table WHERE hash_field = %s"
    assert query.params == [
        b"\x00e\x15\x93\r\x84\xf1\xddw\x0e\x9b\xbb:\x96\xd0\xd1\x8d\xbf0\xb1\xe5`/\x0e\x7f\xa8\x1cy\xeb\x94\x12o\x82>\x08*|\xe2\xf6\x8d2\xbe\xecR\xe1'\x088\xc8\xe4\xbf\x0b\x89P)\x15um\xd2\xebI6RF"
    ]


def test_query_where_on_encrypted_field():
    """Raises a SearchOnEncryptedFieldError exception since a search on an encrypted field is not possible"""

    class TestTable(Table):
        str_field = StrField()

    database = Database("encrypted_mysqldb_user", "encrypted_mysqldb_password", "encrypted_mysqldb_test", Crypt())
    query = Query(database, TestTable)
    with pytest.raises(SearchOnEncryptedFieldError):
        query.where(TestTable.str_field == "text")


def test_query_where_two_times():
    """Fills the query string in the Query object with a search on 2 fields"""

    class TestTable(Table):
        str_field = StrField(encrypted=False)
        int_field = IntField(encrypted=False)

    database = Database("encrypted_mysqldb_user", "encrypted_mysqldb_password", "encrypted_mysqldb_test", Crypt())
    query = Query(database, TestTable)
    query.where(TestTable.str_field == "text").where(TestTable.int_field == 1)
    assert query.query == "SELECT * FROM test_table WHERE str_field = %s AND int_field = %s"
    assert query.params == ["text", 1]


def test_query_first(mocker):
    """Gets a row from the table"""
    mocker.patch(
        "encrypted_mysqldb.crypt.get_decrypted_obj_fields", mocker.Mock(side_effect=(lambda obj_class, fields: fields))
    )

    class TestTable(Table):
        str_field = StrField(encrypted=False)

    database = Database("encrypted_mysqldb_user", "encrypted_mysqldb_password", "encrypted_mysqldb_test", Crypt())
    with database.connection_pool.create_cursor() as cursor:
        cursor.execute("INSERT INTO {0} ({1}) VALUES (%s)".format(TestTable.__tablename__, "str_field"), ["text"])
        cursor.execute("INSERT INTO {0} ({1}) VALUES (%s)".format(TestTable.__tablename__, "str_field"), ["not text"])
    query = Query(database, TestTable)
    result = query.first()
    database.close()
    assert result == TestTable(str_field="text")
    assert result.id == 1


def test_query_first_with_search(mocker):
    """Gets a row from the table depending on search criteria"""
    mocker.patch(
        "encrypted_mysqldb.crypt.get_decrypted_obj_fields", mocker.Mock(side_effect=(lambda obj_class, fields: fields))
    )

    class TestTable(Table):
        str_field = StrField(encrypted=False)

    database = Database("encrypted_mysqldb_user", "encrypted_mysqldb_password", "encrypted_mysqldb_test", Crypt())
    with database.connection_pool.create_cursor() as cursor:
        cursor.execute("INSERT INTO {0} ({1}) VALUES (%s)".format(TestTable.__tablename__, "str_field"), ["not text"])
        cursor.execute("INSERT INTO {0} ({1}) VALUES (%s)".format(TestTable.__tablename__, "str_field"), ["text"])
    result = Query(database, TestTable).where(TestTable.str_field == "text").first()
    database.close()
    assert result == TestTable(str_field="text")
    assert result.id == 2


def test_query_first_with_search_on_id(mocker):
    """Gets a row from the table depending on an id search criteria"""
    mocker.patch(
        "encrypted_mysqldb.crypt.get_decrypted_obj_fields", mocker.Mock(side_effect=(lambda obj_class, fields: fields))
    )

    class TestTable(Table):
        str_field = StrField(encrypted=False)

    database = Database("encrypted_mysqldb_user", "encrypted_mysqldb_password", "encrypted_mysqldb_test", Crypt())
    with database.connection_pool.create_cursor() as cursor:
        cursor.execute("INSERT INTO {0} ({1}) VALUES (%s)".format(TestTable.__tablename__, "str_field"), ["not text"])
        cursor.execute("INSERT INTO {0} ({1}) VALUES (%s)".format(TestTable.__tablename__, "str_field"), ["text"])
    result = Query(database, TestTable).where(TestTable.id == 2).first()
    database.close()
    assert result == TestTable(str_field="text")
    assert result.id == 2


def test_query_first_with_invalid_search():
    """Gets nothing since nothing matches the search criteria"""

    class TestTable(Table):
        str_field = StrField(encrypted=False)

    database = Database("encrypted_mysqldb_user", "encrypted_mysqldb_password", "encrypted_mysqldb_test", Crypt())
    with database.connection_pool.create_cursor() as cursor:
        cursor.execute("INSERT INTO {0} ({1}) VALUES (%s)".format(TestTable.__tablename__, "str_field"), ["text"])
    result = Query(database, TestTable).where(TestTable.str_field == "something").first()
    database.close()
    assert result is None


def test_query_all(mocker):
    """Gets all rows of the table"""
    mocker.patch(
        "encrypted_mysqldb.crypt.get_decrypted_obj_fields", mocker.Mock(side_effect=(lambda obj_class, fields: fields))
    )

    class TestTable(Table):
        str_field = StrField(encrypted=False)

    database = Database("encrypted_mysqldb_user", "encrypted_mysqldb_password", "encrypted_mysqldb_test", Crypt())
    with database.connection_pool.create_cursor() as cursor:
        cursor.execute("INSERT INTO {0} ({1}) VALUES (%s)".format(TestTable.__tablename__, "str_field"), ["text"])
        cursor.execute("INSERT INTO {0} ({1}) VALUES (%s)".format(TestTable.__tablename__, "str_field"), ["not text"])
        cursor.execute("INSERT INTO {0} ({1}) VALUES (%s)".format(TestTable.__tablename__, "str_field"), ["text2"])
    results = Query(database, TestTable).all()
    database.close()
    assert results == [TestTable(str_field="text"), TestTable(str_field="not text"), TestTable(str_field="text2")]
    assert [result.id for result in results] == [1, 2, 3]


def test_query_all_with_search(mocker):
    """Gets all rows of the table matching the search criteria"""
    mocker.patch(
        "encrypted_mysqldb.crypt.get_decrypted_obj_fields", mocker.Mock(side_effect=(lambda obj_class, fields: fields))
    )

    class TestTable(Table):
        str_field = StrField(encrypted=False)

    database = Database("encrypted_mysqldb_user", "encrypted_mysqldb_password", "encrypted_mysqldb_test", Crypt())
    with database.connection_pool.create_cursor() as cursor:
        cursor.execute("INSERT INTO {0} ({1}) VALUES (%s)".format(TestTable.__tablename__, "str_field"), ["text"])
        cursor.execute("INSERT INTO {0} ({1}) VALUES (%s)".format(TestTable.__tablename__, "str_field"), ["not text"])
        cursor.execute("INSERT INTO {0} ({1}) VALUES (%s)".format(TestTable.__tablename__, "str_field"), ["text"])
    results = Query(database, TestTable).where(TestTable.str_field == "text").all()
    database.close()
    assert results == [TestTable(str_field="text"), TestTable(str_field="text")]
    assert [result.id for result in results] == [1, 3]


def test_query_all_with_invalid_search():
    """Gets nothing since nothing matches the search criteria"""

    class TestTable(Table):
        str_field = StrField(encrypted=False)

    database = Database("encrypted_mysqldb_user", "encrypted_mysqldb_password", "encrypted_mysqldb_test", Crypt())
    with database.connection_pool.create_cursor() as cursor:
        cursor.execute("INSERT INTO {0} ({1}) VALUES (%s)".format(TestTable.__tablename__, "str_field"), ["text"])
        cursor.execute("INSERT INTO {0} ({1}) VALUES (%s)".format(TestTable.__tablename__, "str_field"), ["not text"])
        cursor.execute("INSERT INTO {0} ({1}) VALUES (%s)".format(TestTable.__tablename__, "str_field"), ["text"])
    results = Query(database, TestTable).where(TestTable.str_field == "something").all()
    database.close()
    assert results == []


def test_query_delete(mocker):
    """Gets and deletes all rows of the table"""
    mocker.patch(
        "encrypted_mysqldb.crypt.get_decrypted_obj_fields", mocker.Mock(side_effect=(lambda obj_class, fields: fields))
    )

    class TestTable(Table):
        str_field = StrField(encrypted=False)

    database = Database("encrypted_mysqldb_user", "encrypted_mysqldb_password", "encrypted_mysqldb_test", Crypt())
    with database.connection_pool.create_cursor() as cursor:
        cursor.execute("INSERT INTO {0} ({1}) VALUES (%s)".format(TestTable.__tablename__, "str_field"), ["text"])
        cursor.execute("INSERT INTO {0} ({1}) VALUES (%s)".format(TestTable.__tablename__, "str_field"), ["not text"])
        cursor.execute("INSERT INTO {0} ({1}) VALUES (%s)".format(TestTable.__tablename__, "str_field"), ["text2"])
    results = Query(database, TestTable).delete()
    with database.connection_pool.create_cursor() as cursor:
        cursor.execute("SELECT * FROM " + TestTable.__tablename__)
        results_after_deletion = list(cursor.fetchall())
    database.close()
    assert results == [TestTable(str_field="text"), TestTable(str_field="not text"), TestTable(str_field="text2")]
    assert [result.id for result in results] == [0, 0, 0]
    assert results_after_deletion == []


def test_query_delete_with_search(mocker):
    """Gets and deletes all rows of the table matching the search criteria"""
    mocker.patch(
        "encrypted_mysqldb.crypt.get_decrypted_obj_fields", mocker.Mock(side_effect=(lambda obj_class, fields: fields))
    )

    class TestTable(Table):
        str_field = StrField(encrypted=False)

    database = Database("encrypted_mysqldb_user", "encrypted_mysqldb_password", "encrypted_mysqldb_test", Crypt())
    with database.connection_pool.create_cursor() as cursor:
        cursor.execute("INSERT INTO {0} ({1}) VALUES (%s)".format(TestTable.__tablename__, "str_field"), ["text"])
        cursor.execute("INSERT INTO {0} ({1}) VALUES (%s)".format(TestTable.__tablename__, "str_field"), ["not text"])
        cursor.execute("INSERT INTO {0} ({1}) VALUES (%s)".format(TestTable.__tablename__, "str_field"), ["text"])
    results = Query(database, TestTable).where(TestTable.str_field == "text").delete()
    with database.connection_pool.create_cursor() as cursor:
        cursor.execute("SELECT * FROM " + TestTable.__tablename__)
        results_after_deletion = list(cursor.fetchall())
    database.close()
    assert results == [TestTable(str_field="text"), TestTable(str_field="text")]
    assert [result.id for result in results] == [0, 0]
    assert results_after_deletion == [(2, "not text")]


def test_query_delete_with_invalid_search():
    """Gets (and deletes) nothing since nothing matches the search criteria"""

    class TestTable(Table):
        str_field = StrField(encrypted=False)

    database = Database("encrypted_mysqldb_user", "encrypted_mysqldb_password", "encrypted_mysqldb_test", Crypt())
    with database.connection_pool.create_cursor() as cursor:
        cursor.execute("INSERT INTO {0} ({1}) VALUES (%s)".format(TestTable.__tablename__, "str_field"), ["text"])
        cursor.execute("INSERT INTO {0} ({1}) VALUES (%s)".format(TestTable.__tablename__, "str_field"), ["not text"])
        cursor.execute("INSERT INTO {0} ({1}) VALUES (%s)".format(TestTable.__tablename__, "str_field"), ["text"])
    results = Query(database, TestTable).where(TestTable.str_field == "something").delete()
    database.close()
    assert results == []
