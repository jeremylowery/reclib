from cStringIO import StringIO
import datetime
import reclib.validate as V
import reclib.parse.fw as PF
import unittest

class ParseFWTestCase(unittest.TestCase):
    def test_RecordStream(self):
        buf = StringIO("abcdefg")
        stream = PF.RecordStream(buf)
        self.assertEquals(stream.read(1), "a")
        self.assertEquals(stream.get_pos(), 1)
        self.assertEquals(stream.read(6), "bcdefg")
        self.assertEquals(stream.eof, False)
        self.assertEquals(stream.read(1), "")
        self.assertEquals(stream.eof, True)

    def test_Validator(self):
        class MyValidator(V.Validator):
            fields = [
                V.Required("first_name"),
                V.Values("color", ["red", "green", "blue"]),
                V.ISODate("dob")]

        v = MyValidator()
        result = v.validate({"first_name" : "john", "color" : "blue"})
        #print result

    def test_parse_date(self):
        import reclib.parse.fw as P
        h = FixedFieldParseHarness(P.Date("d", 8, "%Y%m%d", min_year=1900))
        value = h("20011230")
        self.assertEquals(value, datetime.date(2001, 12, 30))
        h("18950101")
        self.assertEquals(h.errors[0][1], 'Expected year after 1900')

class FixedFieldParseHarness(object):
    """ Use me to test individual fixed width parse field objects """
    def __init__(self, field):
        self.field = field

    def __call__(self, value):
        self.errors = []
        self.warnings = []
        buf = StringIO(value)
        value = self.field.parse(buf, self.err, self.warn)
        return value

    def err(self, msg, value):
        self.errors.append((value, msg))

    def warn(self, msg, value):
        self.warnings.append((value, msg))

class ParseDelimTestCase(unittest.TestCase):
    def test_parse_date(self):
        import reclib.parse.delim as P
        h = DelimFieldParseHarness(P.Date("d", "%Y%m%d", min_year=1900))
        value = h("20011230")
        self.assertEquals(value, datetime.date(2001, 12, 30))
        h("18950101")
        self.assertEquals(h.errors[0], 'Expected year after 1900')

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
        import reclib.validate as V
        validator = V.DateInPast('dob')
        res = V.RecordValidationResult()
        record = {'dob' : '20230101'}
        validator(record, res)
        self.assertEquals(res[0].field, 'dob')
        self.assertEquals(res[0].msg, 'Value must be in the past.')

        record = {'dob' : '20030101'}
        res = V.RecordValidationResult()
        validator(record, res)
        self.assertEquals(len(res), 0)

if __name__ == '__main__':
    unittest.main()


