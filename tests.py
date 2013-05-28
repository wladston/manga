# -*- coding: utf-8 -*-

# Python.
from datetime import datetime, timedelta

# Python Libs.
import unittest

import manga
from manga import (Document, Model, TimeStampedModel, ValidationError,
                   Field, StringField, EmailField, DateTimeField, DictField,
                   DocumentField, ListField,UTC)


db = manga.setup('_testsuite')

class DBTest(unittest.TestCase):
    def setUp(self):
        assert db.name == '_testsuite'

        for col in db.collection_names():
            db[col].drop() if col != 'system.indexes' else None

    def tearDown(self):
        for col in db.collection_names():
            db[col].drop() if col != 'system.indexes' else None

    def test_field_structure(self):
        """Test the field structure."""

        class Test1(Model):
            field1 = Field()
            field2 = Field()
            field3 = Field()

        m = Test1()

        fields = sorted(m._data.keys())
        fields2 = ['_id', 'field1',  'field2', 'field3']

        self.assertEqual(fields, fields2)

        [self.assertTrue(hasattr(m, x)) for x in fields2]

        m.field1 = 0.38
        m.field2 = 'asdf'
        m.field3 = [{'teste': 123}, 10, 'asdf']

        self.assertEqual(m.field1, 0.38)
        self.assertEqual(m.field2, 'asdf')
        self.assertEqual(m.field3, [{'teste': 123}, 10, 'asdf'])

        data = {'field1': 0.38,
                'field2': 'asdf',
                'field3': [{'teste': 123}, 10, 'asdf'],
                '_id': None}
        self.assertEqual(data, m._data)

    def test_manipulator(self):
        """Test if the manipulator is working properly."""

        class T_NAME12x(Model):
            field1 = Field(blank=True)

        x = T_NAME12x()
        x.save()

        self.assertIsInstance(T_NAME12x.find_one(), T_NAME12x)
        self.assertIsInstance(next(T_NAME12x.find()), T_NAME12x)

    def test_model_redefinition(self):
        class UniqueModel(Model):
            field1 = Field(blank=True)

        with self.assertRaises(Exception) as exc:
            class UniqueModel(Model):
                field1 = Field(blank=False)

        err = 'Manipulator for collection uniquemodel was already defined.'
        self.assertEqual(err, str(exc.exception))

    def test_field_validation(self):
        """Test if validation from field is being correctly run."""

        class TestField(Field):
            def validate(self, value):
                assert value == 'teste'

        class Test(Model):
            f = TestField()

        x = Test()
        x.f = 'teste'

        with self.assertRaises(ValidationError) as exc:
            x.f = '1234'

        expected_str = 'Test: trying to set f <- 1234'
        self.assertEqual(expected_str, str(exc.exception))

        with self.assertRaises(ValidationError) as exc:
            x = Test({'f': 'lalala'})

        with self.assertRaises(ValidationError) as exc:
            x = Test(son={'f': 'lalala'})

    def test_deletion(self):
        """Test if the deletion function works."""

        class TestDel(Model):
            field1 = Field(blank=True)

        x = TestDel()
        x.save()
        self.assertIsNotNone(TestDel.find_one())
        x.delete()
        self.assertIsNone(TestDel.find_one())

        with self.assertRaises(Exception):
            x.delete()

    def test_inheritance(self):
        """Test if field inheritance works as expected."""

        class A(Model):
            fa = Field(default='b')

        class B(A):
            fb = Field(default=10, blank=True)

        class C(B):
            fc = Field(default=[10])

        a = A()
        b = B()
        c = C()

        c_fields_expected = ['_id', 'fa', 'fb', 'fc']
        self.assertEqual(sorted(c._fields.keys()), c_fields_expected)
        self.assertEqual(a._collection, 'a')
        self.assertEqual(b._collection, 'b')
        self.assertEqual(c._collection, 'c')

        c.save()
        c = C.find_one()

        self.assertEqual(c.fc, [10])

    def test_blank(self):
        class TestBlank(Model):
            bl = Field(blank=True)
            nbl = Field(blank=False)

        x = TestBlank()

        x.bl = None

        with self.assertRaises(ValidationError) as exc:
            x.nbl = None

        expected_str = 'TestBlank: trying to set nbl <- None'
        self.assertEqual(expected_str, str(exc.exception))

        with self.assertRaises(Exception):
            x.save()

    def test_default_field_value(self):
        class TestDefault(Model):
            f1 = Field(default='mytest')
            f2 = Field(default={'test': 10})
            f3 = Field(default=[1, 2, 3])
            f4 = Field()

        x = TestDefault()
        self.assertEqual(x.f1, 'mytest')
        self.assertEqual(x.f2, {'test': 10})
        self.assertEqual(x.f3, [1, 2, 3])
        self.assertEqual(x.f4, None)

    def test_to_storage_from_python(self):
        class ComplexNumber(object):
            def __init__(self, real, imaginary):
                self.real = real
                self.imaginary = imaginary

        class ComplexNumberField(Field):
            @staticmethod
            def to_storage(value):
                if value:
                    return [value.real, value.imaginary]
                else:
                    return None

            @staticmethod
            def to_python(value):
                return ComplexNumber(value[0], value[1])

        class TestTSFP(Model):
            nb1 = ComplexNumberField()
            nb2 = ComplexNumberField(default=ComplexNumber(1, 0.13))

        x = TestTSFP()

        self.assertEqual(x.nb2.real, 1)
        self.assertEqual(x.nb2.imaginary, 0.13)

        x.nb1 = ComplexNumber(1.003, 4.521)
        x.save()

        y = TestTSFP.find_one()

        self.assertEqual(y.nb1.real, 1.003)
        self.assertEqual(y.nb1.imaginary, 4.521)
        self.assertEqual(y.nb2.real, 1)
        self.assertEqual(y.nb2.imaginary, 0.13)

    def test_string_field(self):
        class TestString(Model):
            s1 = StringField(default='asdf ', length=(2, 10))
            s2 = StringField(blank=True)
            s3 = StringField(length=(0, 5))
            s4 = StringField()

        x = TestString()

        with self.assertRaises(ValidationError):
            x.s1 = '1       '

        with self.assertRaises(ValidationError):
            x.s1 = '1234567890_'

        x.s3 = 'abc         '

        expected = {'_id': None, 's1': 'asdf', 's2': '', 's3': 'abc', 's4': ''}
        self.assertEqual(x._data, expected)

        with self.assertRaises(ValidationError):
            x.s3 = 10

        with self.assertRaises(ValidationError):
            x.s3 = '         '

        with self.assertRaises(ValidationError):
            x.save()

        x.s4 = 'test'
        x.save()

        y = TestString.find_one()

        self.assertEqual(y.s1, 'asdf')
        self.assertEqual(y.s2, '')
        self.assertEqual(y.s3, 'abc')
        self.assertEqual(y.s4, 'test')

        class TestWrongString(Model):
            a = StringField(default='a', length=(2, 5))

        with self.assertRaises(ValidationError):
            TestWrongString().save()

        class TestWrongString2(Model):
            a = StringField(blank=True, length=(1, 1))

        with self.assertRaises(ValidationError):
            TestWrongString2().save()

    def test_email_field(self):
        class TestEmail(Model):
            em = EmailField()

        x = TestEmail()

        with self.assertRaises(ValidationError):
            x.save()

        with self.assertRaises(ValidationError):
            x.em = 'asdf'

        with self.assertRaises(ValidationError):
            x.em = 'asdf@asas.'

        x.em = 'asdf@asas.as'

    def test_datetime_field(self):
        class TestDateTime(Model):
            dtime = DateTimeField()
            dtime2 = DateTimeField(auto='modified')
            dtime3 = DateTimeField(auto='created')

        x = TestDateTime()

        self.assertIsNone(x.dtime)
        self.assertIsNotNone(x.dtime2)
        self.assertIsNotNone(x.dtime3)

        norm_ms = (x.dtime2.microsecond/1000)*1000
        self.assertEqual(x.dtime2.microsecond, norm_ms)

        with self.assertRaises(Exception):
            x.save()

        with self.assertRaises(ValidationError):
            x.dtime = datetime.now()

        x.dtime = datetime.now(UTC()) - timedelta(days=1)

        x.save()

        x.save()

        self.assertGreater(x.dtime2, x.dtime3)

    def test_dict_field(self):
        class TestDictField(Model):
            dic = DictField()

        x = TestDictField()

        with self.assertRaises(ValidationError):
            x.save()

        with self.assertRaises(ValidationError):
            x.dic = '1234'

        with self.assertRaises(ValidationError):
            x.dic = {}

        x.dic = {'test': 123}

    def test_document_field(self):
        class TestDocument(Document):
            field1 = StringField()

        class TestDocField(Model):
            doc = DocumentField(document=TestDocument)

        x = TestDocField()

        with self.assertRaises(ValidationError):
            x.save()

        with self.assertRaises(ValidationError):
            x.doc = '1234'

        doc = TestDocument()

        with self.assertRaises(ValidationError):
            x.doc = doc

        doc.field1 = 'asdf'
        x.doc = doc

        x.save()

        x = TestDocField().find_one()

        self.assertIsInstance(x.doc, TestDocument)

        self.assertEqual(x.doc.field1, 'asdf')

    def test_timestampedmodel(self):
        class TSM(TimeStampedModel):
            pass

        self.assertIsNotNone(TSM().created)
        self.assertIsNotNone(TSM().modified)

    def test_list_field(self):
        class TestDocument(Document):
            field1 = StringField()

        class TestListField(Model):
            l1 = ListField(field=DocumentField(document=TestDocument))
            l2 = ListField(field=StringField())
            l3 = ListField()

        x = TestListField()

        with self.assertRaises(ValidationError):
            x.save()

        with self.assertRaises(ValidationError):
            x.l3 = '1234'

        x.l3 = ['1234', 3.14, {'hey': 'there'}]

        with self.assertRaises(ValidationError):
            x.l2 = ['1234', 3.14, {'hey': 'there'}]

        x.l2 = ['1234', '3.14', 'hey there']

        with self.assertRaises(ValidationError):
            x.l1 = ['1234']

        x.l1 = [TestDocument({'field1': '1'}), TestDocument({'field1': '2'})]

        x.save()

        x = TestListField().find_one()

        self.assertEqual(x.l1[1].field1, '2')


if __name__ == '__main__':
    unittest.main()
