#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Manga provides a simpler way for working with a MongoDB database.
Copyright (c) 2013, Wladston Viana.
"""

__author__ = 'Wladston Viana'
__version__ = '0.1.6'
__license__ = 'MIT'

# Python.
from re import compile
from datetime import datetime, timedelta, tzinfo

# Pymongo.
from pymongo import MongoClient
from pymongo.son_manipulator import SONManipulator

connection = None
db = None
_manipulators = []

# MongoDB will not store dates with milliseconds.
milli_trim = lambda x: x.replace(microsecond=int((x.microsecond/1000)*1000))


def setup(database_name):
    global db, connection, _manipulators

    if db:
        raise Exception('Module was already configured.')

    connection = MongoClient('localhost', 27017, tz_aware=True)
    db = getattr(connection, database_name)

    for  x in _manipulators:
        db.add_son_manipulator(x)

    return db


class UTC(tzinfo):
    def utcoffset(self, dt):
        return timedelta(0)

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return timedelta(0)


class _ModelManipulator(SONManipulator):
    '''
    Generates on-the-fly manipulators for newly registered models. Keeps track
    of collections already registered, to avoid double registration.
    '''

    _M01 = "Manipulator for collection %s was already defined."
    registered_collections = []

    def __init__(self, cls):
        self.cls = cls
        self.cls_name = cls.__name__.lower()

        if self.cls_name in self.registered_collections:
            raise Exception(self._M01 % self.cls_name)

        else:
            self.registered_collections.append(self.cls_name)

    def transform_outgoing(self, son, collection):
        if son and self.cls_name == collection.name:
            return self.cls(son=son)

        else:
            return son


class ValidationError(Exception):
    def __init__(self, cls, attr, val):
        self.cls = cls
        self.attr = attr
        self.val = val

    def __str__(self):
        return "%s: trying to set %s <- %s" % (self.cls, self.attr, self.val)


class ModelType(type):
    """
    This is a type that generates Model classes properly, setting their
    attributes not to be instances of Field, but rather an API for MongoDB
    itself.
    """

    @staticmethod
    def get_maker(attr):
        def getter(cls, attr=attr):
            return cls._fields[attr].to_python(cls._data.get(attr))

        return getter

    @staticmethod
    def set_maker(attr):
        def setter(cls, val=None, attr=attr):
            try:
                cls._fields[attr].validate(val)

            except AssertionError:
                raise ValidationError(cls.__class__.__name__, attr, val)

            else:
                cls._data[attr] = cls._fields[attr].to_storage(val)

        return setter

    def __new__(cls, name, bases, dct):
        dct.setdefault('_fields', {})
        dct.setdefault('_collection', name.lower())

        for x in bases:
            dct['_fields'].update(getattr(x, '_fields', {}))

        for attr, val in list(dct.items()):
            if isinstance(val, Field):
                dct['_fields'][attr] = val
                dct[attr] = property(cls.get_maker(attr), cls.set_maker(attr))

        rich_cls = super(ModelType, cls).__new__(cls, name, bases, dct)

        if any([x.__name__ == 'Model' for x in bases]):
            if db:
                db.add_son_manipulator(_ModelManipulator(rich_cls))

            else:
                _manipulators.append(_ModelManipulator(rich_cls))

        return rich_cls


class Field(object):
    '''Base field for all fields.'''

    def __init__(self, default=None, blank=False):
        self.blank = blank
        self.default = default

    def validate(self, value):
        if not self.blank:
            assert value

    def pre_save_val(self):
        return None

    @staticmethod
    def to_storage(value):
        return value

    @staticmethod
    def to_python(value):
        return value


class StringField(Field):
    def __init__(self, default='', length=None, **kwargs):
        super(StringField, self).__init__(default, **kwargs)

        self.length = length

    def validate(self, value):
        assert isinstance(value, str)

        if not self.blank:
            assert value.strip()

        if self.length:
            length = len(value.strip())

            assert length >= self.length[0] and length <= self.length[1]

    @staticmethod
    def to_storage(value):
        return value.strip()


class EmailField(StringField):
    email_re = compile(r'^[\S]+@[\S]+\.[\S]+$')

    def __init__(self, default='', length=(5, 100), **kwargs):
        super(EmailField, self).__init__(default, length, **kwargs)

    def validate(self, value):
        super(EmailField, self).validate(value)

        if not self.email_re.match(value):
            raise AssertionError


class DateTimeField(Field):
    def __init__(self, default=None, blank=False, auto=None, **kwargs):
        super(DateTimeField, self).__init__(default, **kwargs)

        self.auto = auto

        if auto in ['modified', 'created']:
            self.default = lambda: datetime.now(UTC())

    def validate(self, value):
        super(DateTimeField, self).validate(value)

        assert (isinstance(value, datetime) and value.tzinfo) or value is None

    def pre_save_val(self):
        return datetime.now(UTC()) if self.auto == 'modified' else None

    @staticmethod
    def to_storage(value):
        return milli_trim(value) if value else None


class DictField(Field):
    def __init__(self, default=None, **kwargs):

        super(DictField, self).__init__(default or {}, **kwargs)

    def validate(self, value):
        assert isinstance(value, dict)

        if not self.blank:
            assert value != {}


class DocumentField(Field):
    def __init__(self, default=None, document=None, **kwargs):
        super(DocumentField, self).__init__(default, **kwargs)

        self.document_class = document

    def validate(self, value):
        if not self.blank:
            assert value

        if value:
            assert isinstance(value, self.document_class)
            value.validate()

        else:
            assert value is None

    @staticmethod
    def to_storage(value):
        return getattr(value, '_data', None)

    def to_python(self, value):
        return self.document_class(son=value)

class ListField(Field):
    def __init__(self, default=None, field=None, **kwargs):
        default = default or []

        super(ListField, self).__init__(default, **kwargs)

        self.field = field

    def validate(self, value):
        assert isinstance(value, list)

        if not self.blank:
            assert value

        [self.field.validate(v) for v in value if self.field]

    def to_storage(self, value):
        if self.field:
            return [self.field.to_storage(v) for v in value]

        else:
            return value

    def to_python(self, value):
        if self.field:
            return [self.field.to_python(v) for v in value]

        else:
            return value


class Document(object, metaclass=ModelType):
    '''
    A MongoDB storable document, without interface to persistant storage. It's
    the base class for Models (with do have persistance) and also embedded
    documents.
    '''

    def __init__(self, data=None, son=None):
        self._data = {}
        validate_exempt = []

        for fname, field in list(self._fields.items()):
            if son and fname in son:
                # val is recovered for validation only.
                val = field.to_python(son.get(fname))

            elif data and fname in data:
                val = data[fname]

            else:
                val = field.default
                val = val() if callable(val) else val

            # Field skips validation if value does not come from son AND no
            # value is given for initialization.
            if not son and not val:
                validate_exempt.append(fname)

            val_storage = son.get(fname) if son else field.to_storage(val)

            self._data[fname] = val_storage

        self.validate(exclude=validate_exempt)

    def validate(self, exclude=None):
        exclude = exclude if exclude else []
        fields = [x for x in self._fields.items() if x[0] not in exclude]

        for fieldname, fieldinstance in fields:
            try:
                python_val = fieldinstance.to_python(self._data[fieldname])
                fieldinstance.validate(python_val)

            except AssertionError:
                val = self._data[fieldname]

                raise ValidationError(self.__class__.__name__, fieldname, val)


class Model(Document, metaclass=ModelType):
    '''Base class for all classes.'''

    # The _id field is required, nevertheless its blank attribute is True.
    # The _id is automatically generated by MongoDB, and doesn't need to be
    # provided.
    _id = Field(blank=True)

    @classmethod
    def find(cls, *args, **kwargs):
        return db[cls._collection].find(*args, **kwargs)

    @classmethod
    def find_one(cls, *args, **kwargs):
        return db[cls._collection].find_one(*args, **kwargs)

    def delete(self):
        if self._id:
            db[self._collection].remove({'_id': self._id})

            self._id = None

        else:
            raise Exception

    def save(self):
        for fieldname, fieldinstance in list(self._fields.items()):
            value = fieldinstance.pre_save_val()

            if value:
                setattr(self, fieldname, value)

        self.validate()

        if self._id:
            spec = {'_id': self._id}

            db[self._collection].update(spec, self._data, upsert=True)

        else:
            del self._data['_id']

            self._data['_id'] = db[self._collection].insert(self._data)


class TimeStampedModel(Model):
    created = DateTimeField(auto='created')
    modified = DateTimeField(auto='modified')
