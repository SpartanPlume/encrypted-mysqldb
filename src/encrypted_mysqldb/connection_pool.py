from mysql.connector import pooling
from mysql.connector import errors as mysql_errors
from mysql.connector import errorcode as mysql_error_codes

from .errors import NoConnectionAvailable
from . import logger


class Cursor:
    def __init__(self, connection):
        self.connection = connection
        self.cursor = connection.cursor(buffered=True)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def __getattr__(self, name):
        return getattr(self.cursor, name)

    def close(self):
        try:
            self.cursor.close()
            logger.debug("Cursor closed")
        except Exception as e:
            logger.exception(e)
        try:
            self.connection.commit()
            logger.debug("Connection committed")
        except Exception as e:
            logger.exception(e)
        try:
            self.connection.close()
            logger.debug("Connection closed")
        except Exception as e:
            logger.exception(e)

    def execute(self, query, params=None):
        logger.debug("Executing query: {0}".format(query))
        # TODO: retry
        try:
            self.cursor.execute(query, params)
        except mysql_errors.Error as e:
            self.close()
            if e.errno != mysql_error_codes.ER_TABLE_EXISTS_ERROR:
                logger.exception(e)
            raise e


class ConnectionPool:
    def __init__(self, user, password, db_name, **options):
        self.user = user
        self.password = password
        self.db_name = db_name
        self.options = options
        self.connect()

    def connect(self):
        self.connection_pool = pooling.MySQLConnectionPool(
            database=self.db_name, user=self.user, password=self.password, **self.options
        )

    def close(self):
        self.connection_pool._remove_connections()

    def create_cursor(self):
        connection = self.connection_pool.get_connection()
        # TODO
        # if not connection:
        #    raise NoConnectionAvailable()
        logger.debug("Connection retrieved from pool")
        return Cursor(connection)
