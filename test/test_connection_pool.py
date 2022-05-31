import subprocess
import pytest

from mysql.connector.errors import ProgrammingError

from encrypted_mysqldb.connection_pool import ConnectionPool


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


def test_connection_pool():
    """Creates a ConnectionPool object"""
    ConnectionPool("encrypted_mysqldb_user", "encrypted_mysqldb_password", "encrypted_mysqldb_test")


def test_connection_invalid_user():
    """Raises a mysql.connector.errors.ProgrammingError exception since the user used is invalid or does not have the rights"""
    with pytest.raises(ProgrammingError):
        ConnectionPool("invalid_user", "password", "encrypted_mysqldb_test")


def test_connection_invalid_database():
    """Raises a mysql.connector.errors.ProgrammingError exception since the database used is invalid"""
    with pytest.raises(ProgrammingError):
        ConnectionPool("encrypted_mysqldb_user", "encrypted_mysqldb_password", "invalid_database")


def test_connection_pool_create_cursor():
    """Creates a Cursor from the ConnectionPool"""
    connection_pool = ConnectionPool("encrypted_mysqldb_user", "encrypted_mysqldb_password", "encrypted_mysqldb_test")
    cursor = connection_pool.create_cursor()
    assert cursor.connection._cnx is not None
    assert cursor._cnx is not None


def test_cursor_close():
    """Creates a Cursor and closes it and the ConnectionPool it is created from"""
    connection_pool = ConnectionPool(
        "encrypted_mysqldb_user", "encrypted_mysqldb_password", "encrypted_mysqldb_test", pool_reset_session=False
    )
    cursor = connection_pool.create_cursor()
    cursor.close()
    assert cursor.connection._cnx is None
    assert cursor._cnx is None


def test_cursor_with():
    """Creates a Cursor using a with clause, closes it and the ConnectionPool it is created from"""
    connection_pool = ConnectionPool(
        "encrypted_mysqldb_user", "encrypted_mysqldb_password", "encrypted_mysqldb_test", pool_reset_session=False
    )
    with connection_pool.create_cursor() as cursor:
        pass
    assert cursor.connection._cnx is None
    assert cursor._cnx is None


def test_cursor_execute():
    """Executes a query with a cursor without exeception"""
    connection_pool = ConnectionPool(
        "encrypted_mysqldb_user", "encrypted_mysqldb_password", "encrypted_mysqldb_test", pool_reset_session=False
    )
    with connection_pool.create_cursor() as cursor:
        cursor.execute(
            "CREATE TABLE encrypted_mysqldb_table (id MEDIUMINT NOT NULL AUTO_INCREMENT, field BLOB, PRIMARY KEY (id))"
        )


def test_cursor_execute_with_args():
    """Executes a query with a cursor without exeception"""
    connection_pool = ConnectionPool(
        "encrypted_mysqldb_user", "encrypted_mysqldb_password", "encrypted_mysqldb_test", pool_reset_session=False
    )
    with connection_pool.create_cursor() as cursor:
        cursor.execute(
            "CREATE TABLE encrypted_mysqldb_table (id MEDIUMINT NOT NULL AUTO_INCREMENT, field MEDIUMINT, PRIMARY KEY (id))"
        )
        cursor.execute("INSERT INTO encrypted_mysqldb_table (field) VALUES (%s)", [123])
