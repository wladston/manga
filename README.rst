Manga, a sweet MongoDB abstraction layer
========================================

Manga provides a simpler way for working with a MongoDB database.
It is provided in a single python source file with no dependencies other than
the Python Standard Library and Pymongo.

License: MIT (see LICENSE)

Installation and Dependencies
-----------------------------

Install bottle with ``pip install manga`` or just download manga.py and place
it in your project directory. Manga onle depends on Pymongo.

Example
-------

.. code-block:: python

    from manga import setup, Model, StringField, EmailField

    setup('test_database')

    class User(Model):
        name = StringField(length=(2, 10))
        email = EmailField(required=True)

    bob = User({'name': 'Bob', 'email': 'bobby@tables.com'})
    bob.save()
