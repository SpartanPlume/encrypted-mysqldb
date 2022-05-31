import copy

import inflection

from .fields.base_field import BaseField
from .fields import HashField, IdField, DatetimeField


def get_real_table_attribute(cls, __name):
    try:
        return type.__getattribute__(cls, __name)
    except Exception:
        for base in cls.__bases__:
            if issubclass(base, Table):
                try:
                    return get_real_table_attribute(base, __name)
                except Exception:
                    continue
        raise


class TableOperator:
    def __init__(self, name):
        self.__name = name

    def __eq__(self, value):
        return (self.__name, value)


class TableMetaclass(type):
    def __getattribute__(cls, __name):
        if __name == "__tablename__":
            try:
                return type.__getattribute__(cls, __name)
            except Exception:
                return inflection.underscore(cls.__name__)
        try:
            attribute = get_real_table_attribute(cls, __name)
            if (
                not __name.startswith("_")
                and not callable(attribute)
                and not isinstance(attribute, (property, classmethod))
            ):
                return TableOperator(__name)
        except Exception:
            pass
        return type.__getattribute__(cls, __name)


class Table(metaclass=TableMetaclass):
    id = IdField()

    def __init__(self, database=None, **kwargs):
        self._database = database
        self.__tablename__ = type(self).__tablename__
        self._set_parent_class_attributes(type(self))
        self.update(**kwargs)

    def _set_parent_class_attributes(self, cls):
        for base_cls in cls.__bases__:
            if issubclass(base_cls, Table):
                self._set_parent_class_attributes(base_cls)
        for key, value in vars(cls).items():
            try:
                attribute = get_real_table_attribute(cls, key)
                if (
                    not key.startswith("_")
                    and not callable(attribute)
                    and not isinstance(attribute, (property, classmethod))
                ):
                    setattr(self, key, copy.deepcopy(value))
            except Exception:
                continue

    def __eq__(self, __o):
        if not __o:
            return False
        for key, value in self.get_table_dict().items():
            if key != "id" and key in vars(__o) and value != getattr(__o, key):
                return False
        return True

    def __deepcopy__(self, memo):
        new_obj = self.__class__(self._database)
        for key, value in self.get_table_dict().items():
            setattr(new_obj, key, copy.deepcopy(value, memo))
        return new_obj

    def __getattribute__(self, __name):
        attribute = object.__getattribute__(self, __name)
        if isinstance(attribute, BaseField):
            return attribute.value
        return attribute

    @classmethod
    def get_from_id(cls, database, obj_id):
        return database.query(cls).where(cls.id == obj_id).first()

    def get_table_dict(self):
        table_dict = {}
        for key, value in vars(self).items():
            try:
                class_value = get_real_table_attribute(type(self), key)
            except Exception:
                continue
            if isinstance(class_value, BaseField):
                if isinstance(value, BaseField):
                    table_dict[key] = value.value
                else:
                    table_dict[key] = value
        return table_dict

    def get_api_dict(self):
        table_dict = self.get_table_dict()
        api_dict = {}
        for key, value in table_dict.items():
            class_value = get_real_table_attribute(type(self), key)
            if isinstance(class_value, DatetimeField):
                api_dict[key] = value.isoformat()
            elif not isinstance(class_value, HashField):
                api_dict[key] = value
        return api_dict

    def get_complete_api_dict(self):
        complete_dict = self.get_api_dict()
        for key, value in vars(type(self)).items():
            if isinstance(value, property):
                sub_object = getattr(self, key)
                try:
                    if isinstance(sub_object, list):
                        sub_dict = [obj.get_complete_api_dict() for obj in sub_object]
                        complete_dict[key] = sub_dict
                    else:
                        complete_dict[key] = sub_object.get_complete_api_dict()
                except AttributeError:
                    continue
        return complete_dict

    def update(self, arg_dict={}, **kwargs):
        for key, value in {**arg_dict, **kwargs}.items():
            try:
                class_value = get_real_table_attribute(type(self), key)
            except Exception:
                continue
            if isinstance(class_value, BaseField):
                field_value = copy.deepcopy(class_value)
                field_value.value = value
                setattr(self, key, field_value)

    def delete(self):
        self._database.delete(self)
