import copy
import datetime

from encrypted_mysqldb.fields import (
    IdField,
    BoolField,
    DatetimeField,
    HashField,
    IntField,
    ListField,
    SetField,
    StrField,
)
from encrypted_mysqldb.table import Table, TableOperator


def test_empty_table():
    """Creates an empty table"""

    class EmptyTable(Table):
        pass

    assert EmptyTable.__tablename__ == "empty_table"
    table = EmptyTable()
    assert table.__tablename__ == "empty_table"


def test_override_tablename():
    """Creates a table with defined tablename instead of using class name"""

    class OverrideTableName(Table):
        __tablename__ = "another_name"

    assert OverrideTableName.__tablename__ == "another_name"
    table = OverrideTableName()
    assert table.__tablename__ == "another_name"


def test_table_with_fields():
    """Creates the table"""

    class TableWithFields(Table):
        datetime_field = DatetimeField()
        hash_field = HashField("text")
        int_field = IntField()
        list_field = ListField(IntField, [1, 3, 6])
        set_field = SetField(StrField)
        str_field = StrField()

    TableWithFields()


def test_table_with_fields_and_given_values_in_init():
    """Creates the table with the correct values given in the constructor"""

    class TableWithNoDefaultValue(Table):
        int_field = IntField()
        str_field = StrField()

    table = TableWithNoDefaultValue(id=1, int_field=2, str_field="abc")
    assert table.id == 1
    assert table.int_field == 2
    assert table.str_field == "abc"


def test_table_with_fields_trying_to_init_inexistant_field():
    """Ignores the field and creates the table without raising an exception"""

    class TableWithMissingField(Table):
        pass

    TableWithMissingField(a=1)


def test_table_with_non_field_attribute():
    """Ignores the field and creates the table without raising an exception"""

    class TableWithNonFieldAttribute(Table):
        field = int()

    TableWithNonFieldAttribute(field=1)


def test_table_equality():
    """Returns True"""

    class TableEquality(Table):
        str_field = StrField()

    assert TableEquality(id=1) == TableEquality(id=2)


def test_table_inequality_with_none():
    """Returns False"""

    class TableEquality(Table):
        str_field = StrField()

    other = None
    assert TableEquality(id=1) != other


def test_table_inequality():
    """Returns False"""

    class TableInequality(Table):
        str_field = StrField()

    assert TableInequality(str_field="abc") != TableInequality(str_field="def")


def test_get_attribute_of_field_returns_value():
    """Returns field value"""

    class TableWithField(Table):
        str_field = StrField("abc")

    assert TableWithField().str_field == "abc"


def test_get_table_dict():
    """Gets the table as dictionary, ignores non field attributes"""

    class TableWithFieldsAndNonField(Table):
        bool_field = BoolField(True)
        datetime_field = DatetimeField(datetime.datetime(2020, 1, 2, 3, 4, 5))
        hash_field = HashField("text")
        int_field = IntField(2, with_hash=True)
        list_field = ListField(IntField, [1, 3, 6])
        str_field = StrField("abc", encrypted=True)
        non_field = 123

    expected_dict = {
        "id": 0,
        "bool_field": True,
        "datetime_field": datetime.datetime(2020, 1, 2, 3, 4, 5),
        "hash_field": "text",
        "int_field": 2,
        "list_field": [1, 3, 6],
        "str_field": "abc",
    }
    a = TableWithFieldsAndNonField()
    assert a.get_table_dict() == expected_dict


def test_get_subtable_dict():
    """Gets the table as dictionary, ignores non field attributes"""

    class TableWithFieldsAndNonField(Table):
        hash_field = HashField("text")
        int_field = IntField(2, with_hash=True)

    class SubtableWithFieldsAndNonField(TableWithFieldsAndNonField):
        list_field = ListField(IntField, [1, 3, 6])
        str_field = StrField("abc", encrypted=True)
        non_field = 123

    expected_dict = {"id": 0, "hash_field": "text", "int_field": 2, "list_field": [1, 3, 6], "str_field": "abc"}
    a = SubtableWithFieldsAndNonField()
    assert a.get_table_dict() == expected_dict


def test_get_api_dict():
    """Gets the table as dictionary without hash fields and ignores non field attributes"""

    class TableWithFieldsAndNonField(Table):
        datetime_field = DatetimeField(datetime.datetime(2020, 1, 2, 3, 4, 5))
        hash_field = HashField("text")
        int_field = IntField(2, with_hash=True)
        list_field = ListField(IntField, [1, 3, 6])
        str_field = StrField("abc", encrypted=True)
        non_field = 123

    expected_dict = {
        "id": 1,
        "datetime_field": "2020-01-02T03:04:05",
        "int_field": 2,
        "list_field": [1, 3, 6],
        "str_field": "abc",
    }
    assert TableWithFieldsAndNonField(id=1).get_api_dict() == expected_dict


def test_get_complete_api_dict():
    """Gets the table as dictionary with property reference tables, without hash fields and ignores non field attributes and non sub tables property"""

    class ReferenceTable(Table):
        sub_str_field = StrField("def")

    class ReferenceTableOfList(Table):
        sub_of_list_int_field = IntField()

    class TableWithFieldsAndNonField(Table):
        def __init__(self, database=None, **kwargs):
            super().__init__(database, **kwargs)
            self._sub_table = None
            self._sub_tables_of_list = []

        hash_field = HashField("text")
        int_field = IntField(2, with_hash=True)
        list_field = ListField(IntField, [1, 3, 6])
        str_field = StrField("abc", encrypted=True)
        non_field = 123
        sub_table_id = IdField(1)
        sub_tables_of_list_ids = ListField(IdField, [0, 1])

        @property
        def sub_table(self):
            return ReferenceTable(id=1)

        @property
        def sub_tables_of_list(self):
            return [ReferenceTableOfList(sub_of_list_int_field=3), ReferenceTableOfList(id=1, sub_of_list_int_field=4)]

        @property
        def something(self):
            return 2

    expected_dict = {
        "id": 1,
        "int_field": 2,
        "list_field": [1, 3, 6],
        "str_field": "abc",
        "sub_table": {"id": 1, "sub_str_field": "def"},
        "sub_table_id": 1,
        "sub_tables_of_list": [{"id": 0, "sub_of_list_int_field": 3}, {"id": 1, "sub_of_list_int_field": 4}],
        "sub_tables_of_list_ids": [0, 1],
    }
    assert TableWithFieldsAndNonField(id=1).get_complete_api_dict() == expected_dict


def test_deepcopy_table():
    """Deepcopies the table entirely"""

    class TableToDeepcopy(Table):
        list_field = ListField(IntField)
        str_field = StrField()

    initial_table = TableToDeepcopy(id=1, list_field=[1, 3, 6], str_field="abc")
    copy_table = copy.deepcopy(initial_table)
    assert copy_table is not initial_table
    assert copy_table == initial_table


def test_update():
    """Updates the table with given values and ignores non existing key"""

    class TableToUpdate(Table):
        some_object_id_field = IdField()
        int_field = IntField()
        list_field = ListField(StrField)
        str_field = StrField()

    table = TableToUpdate()
    table.update(some_object_id_field=2, int_field=123, list_field=["a", "b", "c"], str_field="def", something=1)
    assert table.some_object_id_field == 2
    assert table.int_field == 123
    assert table.list_field == ["a", "b", "c"]
    assert table.str_field == "def"


def test_table_operator_eq():
    """eq operator of TableOperator returns a tuple of its constructor parameter and the compared value"""
    table_operator = TableOperator("test")
    eq = table_operator == "something"
    assert eq == ("test", "something")


def test_get_attribute_on_table_class():
    """Returns a TableOperator with the name of the field as constructor parameter"""

    class TestTable(Table):
        str_field = StrField()

    assert TestTable.str_field == TableOperator("str_field")
