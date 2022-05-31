import datetime

from mysql.connector import errors as mysql_errors
from mysql.connector import errorcode as mysql_error_codes

from . import init_crypt, crypt, logger
from .connection_pool import ConnectionPool
from .errors import DatabaseInitializationError, InvalidCryptError, NotTableTypeError, SearchOnEncryptedFieldError
from .table import Table
from .fields import HashField, IntField, IdField, DatetimeField, BoolField


class Query:
    def __init__(self, database, obj_class):
        self.database = database
        self.obj_class = obj_class
        self.query = "SELECT * FROM " + self.obj_class.__tablename__
        self.params = []
        self.first_where_use = True

    def where(self, *args, **kwargs):
        arguments = {**dict(args), **kwargs}
        for key, value in arguments.items():
            if not value:
                value = "NULL"
            if self.first_where_use:
                self.first_where_use = False
                self.query += " WHERE "
            else:
                self.query += " AND "
            class_field = object.__getattribute__(self.obj_class(), key)
            class_field.value = value
            if class_field.with_hash:
                self.query += key + "_hash = %s"
                self.params.append(class_field.hash())
            elif isinstance(class_field, HashField):
                self.query += key + " = %s"
                self.params.append(class_field.hash())
            elif not class_field.encrypted:
                self.query += key + " = %s"
                self.params.append(class_field.value)
            else:
                logger.debug("Searching on encrypted field, raising error")
                raise SearchOnEncryptedFieldError()
        return self

    def first(self):
        cursor = self.database.connection_pool.create_cursor()
        if self.params:
            cursor.execute(self.query, self.params)
        else:
            cursor.execute(self.query)
        result = cursor.fetchone()
        if result:
            new_result = dict()
            for column, value in zip(cursor.cursor._description, result):
                new_result[column[0]] = value
            result = new_result
        cursor.close()
        if not result:
            return None
        return self.obj_class(self.database, **crypt.get_decrypted_obj_fields(self.obj_class, result))

    def all(self):
        cursor = self.database.connection_pool.create_cursor()
        if self.params:
            cursor.execute(self.query, self.params)
        else:
            cursor.execute(self.query)
        results = list(cursor.fetchall())
        if results:
            new_results = []
            for result in results:
                new_result = dict()
                for column, value in zip(cursor.cursor._description, result):
                    new_result[column[0]] = value
                new_results.append(new_result)
            results = new_results
        cursor.close()
        if not results:
            return []
        to_return = []
        for result in results:
            to_return.append(self.obj_class(self.database, **crypt.get_decrypted_obj_fields(self.obj_class, result)))
        return to_return

    def delete(self):
        results = self.all()
        for result in results:
            result.delete()
            result.id = 0
        return results


class Database:
    def __init__(self, user, password, db_name, crypt_obj, **connection_pool_options):
        if (
            not crypt_obj
            or not callable(getattr(crypt_obj, "encrypt", None))
            or not callable(getattr(crypt_obj, "decrypt", None))
        ):
            raise InvalidCryptError()
        self.db_name = db_name
        init_crypt(crypt_obj)
        try:
            self.connection_pool = ConnectionPool(user, password, db_name, **connection_pool_options)
            self._init_tables(Table.__subclasses__())
        except mysql_errors.Error as e:
            logger.exception(e)
            raise DatabaseInitializationError(e)
        logger.info("Database {0} is ready".format(db_name))

    def close(self):
        self.connection_pool.close()

    def _init_tables(self, tables):
        for table in tables:
            if subtables := table.__subclasses__():
                self._init_tables(subtables)
            elif table.__tablename__:
                self._create_table(table)

    def _get_table_fields_with_type(self, obj_instance, table_fields):
        table_fields_with_type = []
        for table_field in table_fields:
            if table_field == "id":
                table_fields_with_type.append("id MEDIUMINT NOT NULL AUTO_INCREMENT PRIMARY KEY")
                continue
            class_field = object.__getattribute__(obj_instance, table_field)
            if class_field.with_hash:
                table_fields_with_type.append(table_field + "_hash BLOB")
            if class_field.encrypted or isinstance(class_field, HashField):
                table_fields_with_type.append(table_field + " BLOB")
            elif isinstance(class_field, (IdField, IntField)):
                table_fields_with_type.append(table_field + " MEDIUMINT")
            elif isinstance(class_field, BoolField):
                table_fields_with_type.append(table_field + " BOOL")
            elif isinstance(class_field, DatetimeField):
                table_fields_with_type.append(table_field + " DATETIME")
            else:
                table_fields_with_type.append(table_field + " TEXT")
        return table_fields_with_type

    def _create_table(self, obj_class):
        obj_instance = obj_class(self)
        table_fields_with_type = self._get_table_fields_with_type(obj_instance, obj_instance.get_table_dict().keys())
        query = (
            "SELECT * FROM information_schema.tables WHERE table_schema = '{0}' AND table_name = '{1}' LIMIT 1".format(
                self.db_name, obj_class.__tablename__
            )
        )
        rowcount = 0
        with self.connection_pool.create_cursor() as cursor:
            cursor.execute(query)
            rowcount = cursor.rowcount
        logger.info(rowcount)
        if rowcount:
            self._update_table(obj_class)
        else:
            query = "CREATE TABLE {0} ({1})".format(obj_class.__tablename__, ", ".join(table_fields_with_type))
            with self.connection_pool.create_cursor() as cursor:
                cursor.execute(query)

    def _update_table(self, obj_class):
        obj_instance = obj_class(self)
        query = "DESC {0}".format(obj_class.__tablename__)
        current_columns = set()
        with self.connection_pool.create_cursor() as cursor:
            cursor.execute(query)
            current_columns = set([column[0] for column in cursor.fetchall()])
        table_fields = obj_instance.get_table_dict().keys()
        obj_columns = set(table_fields)
        columns_to_add = self._get_table_fields_with_type(obj_instance, obj_columns - current_columns)
        columns_to_delete = current_columns - obj_columns
        if columns_to_add:
            query = "ALTER TABLE {0} ADD COLUMN {1}".format(
                obj_class.__tablename__, ", ADD COLUMN ".join(columns_to_add)
            )
            with self.connection_pool.create_cursor() as cursor:
                cursor.execute(query)
                logger.info(
                    "Table {0} has been updated with new columns: {1}".format(
                        obj_class.__tablename__, ",".join(columns_to_add)
                    )
                )
        if columns_to_delete:
            query = "ALTER TABLE {0} DROP COLUMN {1}".format(
                obj_class.__tablename__, ", DROP COLUMN ".join(columns_to_delete)
            )
            with self.connection_pool.create_cursor() as cursor:
                cursor.execute(query)
                logger.info(
                    "Table {0} has been updated with removed columns: {1}".format(
                        obj_class.__tablename__, ",".join(columns_to_add)
                    )
                )

    def add(self, obj):
        if not isinstance(obj, Table):
            raise NotTableTypeError()
        obj._database = self
        if "created_at" in obj.__dict__:
            obj.created_at = datetime.datetime.utcnow()
        if "updated_at" in obj.__dict__:
            obj.updated_at = datetime.datetime.utcnow()
        encrypted_fields = crypt.get_encrypted_obj_fields(obj)
        encrypted_fields.pop("id", 0)
        if encrypted_fields:
            keys, values = zip(*encrypted_fields.items())
        else:
            keys, values = [], []
        query = "INSERT INTO {0} ({1}) VALUES ({2})".format(
            obj.__tablename__, ", ".join(keys), ", ".join(["%s"] * len(keys))
        )
        with self.connection_pool.create_cursor() as cursor:
            cursor.execute(query, values)
            obj.id = cursor.lastrowid
            logger.info("Object {0} with id {1} has been added".format(obj.__tablename__, obj.id))
        return obj

    def update(self, obj):
        if not isinstance(obj, Table):
            raise NotTableTypeError()
        if "updated_at" in obj.__dict__:
            obj.updated_at = datetime.datetime.utcnow()
        encrypted_fields = crypt.get_encrypted_obj_fields(obj)
        obj_id = encrypted_fields.pop("id", 0)
        if obj_id <= 0:
            return obj
        query_set_keys = [query_set_key + " = %s" for query_set_key in encrypted_fields.keys()]
        query = "UPDATE {0} SET {1} WHERE id = {2}".format(obj.__tablename__, ", ".join(query_set_keys), obj_id)
        with self.connection_pool.create_cursor() as cursor:
            cursor.execute(query, list(encrypted_fields.values()))
            logger.info("Object {0} with id {1} has been updated".format(obj.__tablename__, obj.id))
        return obj

    def delete(self, obj):
        if not isinstance(obj, Table):
            raise NotTableTypeError()
        query = "DELETE FROM {0} WHERE id = {1}".format(obj.__tablename__, obj.id)
        with self.connection_pool.create_cursor() as cursor:
            cursor.execute(query)
            logger.info("Object {0} with id {1} has been deleted".format(obj.__tablename__, obj.id))
        obj.id = 0
        return obj

    def query(self, obj_class):
        if not isinstance(obj_class, type) or not issubclass(obj_class, Table):
            raise NotTableTypeError()
        return Query(self, obj_class)
