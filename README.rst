Manga, a sweet MongoDB abstraction layer
========================================

Manga provides a simpler way for working with a MongoDB database.
It is provided in a single python source file with no dependencies other than
the Python Standard Library and Pymongo.

License: MIT (see LICENSE)

Installation and Dependencies
-----------------------------

Install manga with ``pip install manga`` or just download manga.py and place
it in your project directory. Manga onle depends on Pymongo.

Example
-------

.. code-block:: python

    from manga import setup, Model, StringField, EmailField

    setup('test_database')

    class User(Model):
        name = StringField(length=(2, 10))
        email = EmailField()

    bob = User({'name': 'Bob', 'email': 'bobby@tables.com'})
    bob.save()


Tutorial
--------
This is a step-by-step guide demostrating how to work with Manga. At this time
Manga can only handle one database at a time, and before doing anything, we
should tell Manga with database is that:

.. code-block:: python

    >>> from manga import setup
    >>> setup('tutorial')
    Database(MongoClient('localhost', 27017), 'tutorial')

Now, to define a collection of data, declare a class that inherits from Model:

.. code-block:: python

    >>> from manga import Model
    >>> class FirstModel(Model):
    ...     pass
    ...
    >>> obj = FirstModel()

Model objects have a default "_id" field, that is automatically populated once
the object is saved. You can also specify a custom _id if you want:

.. code-block:: python

    >>> obj.save()
    >>> obj._id
    ObjectId('51acbe4bd2eee6cc857768e6')
    >>> obj2 = FirstModel()
    >>> obj2._id = 'my custom id'
    >>> obj2.save()
    >>> obj2._id
    'my custom id'

Models have pymongo's find and find_one methods. The objects returned will
be validated (to see if they match the Model's schema) and then will be
returned as Model objects:

.. code-block:: python

    >>> FirstModel.find_one()
    <__main__.FirstModel object at 0x104ea7450>
    >>> [x._id for x in FirstModel.find()]
    [ObjectId('51acbe4bd2eee6cc857768e6'), 'my custom id']

Of course you will want to create Models storing more than an _id field.
In Manga that is done by defining attributes to the Model with are
instances of Field. Fields can take a blank parameter, with defaults to
False (by default a field value can't be blank).  A default parameter can
also be specified:

.. code-block:: python

    >>> from manga import Field
    >>> class Person(Model):
    ...     name = Field()
    ...     motto = Field(default="Be happy.")
    ...     notes = Field(blank=True)
    ...
    >>>

Now Manga will make sure your data is valid before writing it to persistance.
You also won't be able to assign invalid values to any of the fields:

.. code-block:: python

    >>> p1 = Person()
    >>> p1.save()
    Traceback (most recent call last):
    [...]
    manga.ValidationError: Person: trying to set name <- None
    >>> p1.name = ''
    manga.ValidationError: Person: trying to set name <-
    >>>

Now, let's create some persons. Note the alternative way for defining field
values when instantiating the Model class. Also, see how internal object's
data can be seen with the "_data" attribute:

.. code-block:: python

    >>> joe = Person()
    >>> joe.name = "John Snow"
    >>> joe.save()
    >>> joe.name
    'John Snow'
    >>> joe._id
    ObjectId('51acd1f9d2eee6d07e073794')
    >>> joe.motto
    'Be happy.'
    >>> joe.notes
    >>> tesla = Person({'name': 'Nikola Tesla', 'motto': 'Free energy'})
    >>> tesla.save()
    >>> tesla._data
    {'name': 'Nikola Tesla', 'motto': 'Free energy',
    '_id': ObjectId('51acd2c6d2eee6d07e073795'), 'notes': None}
    >>> edison = Person({'name': 'Thomas Edison', 'motto': 'DC power'})
    >>> edison.notes = ["Didn't like Tesla"]
    >>> edison.save()
    >>> edison._data
    {'name': 'Thomas Edison', 'motto': 'DC power',
    '_id': ObjectId('51acd442d2eee6d07e073796'),
    'notes': ["Didn't like Tesla"]}
    >>>

You can create Model classes that inherit from other Model classes:

.. code-block:: python

    >>> class SuperHero(Person):
    ...     superpowers = Field()
    ...
    >>> superman = SuperHero({'name': 'Clark Kent',
    ...                       'superpowers': ['strength', 'speed', 'flight']})
    >>> superman.save()
    >>> superman._data
    {'superpowers': ['strength', 'speed', 'flight'], 'name': 'Clark Kent',
    'motto': 'Be happy.', '_id': ObjectId('51acd555d2eee6d07e073797'),
    'notes': None}
    >>>

With Manga, you can extend Fields to validate and represent any type of
data, here is an example with Complex Numbers:

.. code-block:: python

    >>> class ComplexNumber(object):
    ...     def __init__(self, real, imaginary):
    ...         self.real = real; self.imaginary = imaginary
    ...
    >>> class ComplexNumberField(Field):
    ...     @staticmethod
    ...     def to_storage(value):
    ...             return [value.real, value.imaginary] if value else None
    ...     @staticmethod
    ...     def to_python(value):
    ...         return ComplexNumber(value[0], value[1]) if value else None
    ...
    >>> class TheNumbers(Model):
    ...     number1 = ComplexNumberField()
    ...     number2 = ComplexNumberField(blank=True)
    ...
    >>> x = TheNumbers({'number1': ComplexNumber(1.234, 4.321)})
    >>> x.save()
    >>> x.number1.real
    1.234
    >>> x._data
    {'number2': None, 'number1': [1.234, 4.321], '_id': ObjectId('51acd940d2eee6d07e073798')}
    >>>

One more field example, this time showing how to perform validation:

.. code-block:: python

    >>> class PositiveIntegerField(Field):
    ...     def validate(self, value):
    ...         assert int(value) and value >= 0
    ...
    >>> class Numbers2(Model):
    ...     n1 = PositiveIntegerField()
    ...
    >>> x = Numbers2()
    >>> x.n1 = -10
    Traceback (most recent call last):
    [...]
    manga.ValidationError: Numbers2: trying to set n1 <- -10
    >>> x.n1 = 10
    >>>

Manga ships with some basic Fields, such as the StringField, DateTimeField,
DictField, ListField, EmailField, and in the future many more. Check out the
source to avoid to define vanilla fields in your code. If you define any
interesting, generic and reusable Field, send me a pull request.

Now, the most interesting Field out there is the DocumentField. It lets you
embbed Documents (defined with fields just like Models) within other Models.
Here is a short example:

.. code-block:: python

    >>> from manga import Document, DocumentField, StringField
    >>> class Rectangle(Document):
    ...     v1 = PositiveIntegerField()
    ...     v2 = PositiveIntegerField()
    ...
    >>> class SimpleDrawing(Model):
    ...    title = StringField(length=(2,10))
    ...    rect = DocumentField(document=Rectangle)
    ...
    >>> rect = Rectangle({'v1': 10, 'v2': 5})
    >>> x = SimpleDrawing({'title': 'art', 'rect': rect})
    >>> x.save()
    >>> x.rect
    <__main__.Rectangle object at 0x10e8f3ad0>
    >>> x.rect.v1
    10
    >>>


