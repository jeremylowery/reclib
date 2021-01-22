from builtins import next
from builtins import object
import logging
import datetime
import unittest

import six

import reclib.validate as V
import reclib.parse.fw as PF
import reclib.parse.delim as P

logging.basicConfig(level=logging.DEBUG)

class ParseFWTestCase(unittest.TestCase):
    def test_RecordStream(self):
        buf = six.StringIO("abcdefg")
        stream = PF.RecordStream(buf)
        stream.move_next()
        self.assertEqual(stream.read(1), "a")
        self.assertEqual(stream.get_pos(), 1)
        self.assertEqual(stream.read(6), "bcdefg")
        self.assertEqual(stream.eof, False)
        self.assertEqual(stream.read(1), "")
        stream.move_next()
        self.assertEqual(stream.eof, True)

    def test_Validator(self):
        class MyValidator(V.Validator):
            fields = [
                V.Required("first_name"),
                V.Values("color", ["red", "green", "blue"]),
                V.ISODate("dob")]

        v = MyValidator()
        result = v.validate({"first_name" : "john", "color" : "blue"})

    def test_parse_date(self):
        import reclib.parse.fw as P
        h = FixedFieldParseHarness(P.Date("d", 8, "%Y%m%d", min_year=1900))
        value = h("20011230")
        self.assertEqual(value, datetime.date(2001, 12, 30))
        h("18950101")
        self.assertEqual(h.errors[0][1], 'Expected year after 1900')

    def test_parse_datetime(self):
        import reclib.parse.fw as P
        h = FixedFieldParseHarness(P.Datetime("d", "YYYYMMDDHHMM"))
        value = h("200112301430")
        self.assertEqual(value, datetime.datetime(2001, 12, 30, 14, 30, 0))

class FixedFieldParseHarness(object):
    """ Use me to test individual fixed width parse field objects """
    def __init__(self, field):
        self.field = field

    def __call__(self, value):
        self.errors = []
        self.warnings = []
        buf = six.StringIO(value)
        value = self.field.parse(buf, self.err, self.warn)
        return value

    def err(self, msg, value):
        self.errors.append((value, msg))

    def warn(self, msg, value):
        self.warnings.append((value, msg))

class ParseDelimTestCase(unittest.TestCase):
    def test_parse_date(self):
        h = DelimFieldParseHarness(P.Date("d", "%Y%m%d", min_year=1900))
        value = h("20011230")
        self.assertEqual(value, datetime.date(2001, 12, 30))
        h("18950101")
        self.assertEqual(h.errors[0], 'Expected year after 1900')

    def test_tab_delim(self):
        b = six.StringIO("""\
a\tb\tc
d\te\tf
""")
        p = P.Parser()
        p.fields = [
            P.String("foo"),
            P.String("bar"),
            P.String("baz"),
        ]
        p.delimiter = "\t"
        recs = iter(p.parse(b))
        self.assertEqual(next(recs), {'baz': 'c', 'foo': 'a', 'bar': 'b'})
        self.assertEqual(next(recs), {'baz': 'f', 'foo': 'd', 'bar': 'e'})

class DelimFieldParseHarness(object):
    """ Use me to test individual delimited parse field objects """
    def __init__(self, field):
        self.field = field

    def __call__(self, value):
        self.errors = []
        self.warnings = []
        value = self.field.parse(value, self.err, self.warn)
        return value

    def err(self, msg):
        self.errors.append(msg)

    def warn(self, msg):
        self.warnings.append(msg)

class ValidatorTestCase(unittest.TestCase):
    def test_DateInPast(self):
        validator = V.DateInPast('dob')
        res = V.RecordValidationResult()
        record = {'dob' : '20230101'}
        validator(record, res)
        self.assertEqual(res[0].field, 'dob')
        self.assertEqual(res[0].msg, 'Value must be in the past.')

        record = {'dob' : '20030101'}
        res = V.RecordValidationResult()
        validator(record, res)
        self.assertEqual(len(res), 0)

    def test_length_validator(self):
        validator = V.Length('first_name', max=12)
        res = V.RecordValidationResult()
        record = {'first_name' : 'john'}
        validator(record, res)
        self.assertEqual(len(res), 0)
        validator({'first_name': 'xxxxxxxfasdfasdf'}, res)
        self.assertEqual(len(res), 1)

if __name__ == '__main__':
    unittest.main()

