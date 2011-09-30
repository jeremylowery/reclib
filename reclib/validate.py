"""
See reclib.ut for usage
"""
import datetime
import time

class Validator(object):
    checks = []

    def validate(self, record):
        result = RecordValidationResult()
        for field in self.checks:
            field(record, result)
        return result

class RecordValidationResult(list):

    def error(self, field, msg, *a):
        if a: msg %= a
        self.append(RecordError(field, msg))

    def __str__(self):
        return "\n".join([str(s) for s in self])
    
class RecordError(object):
    def __init__(self, field, msg):
        self.field = field
        self.msg = msg

    def __str__(self):
        if self.field is None:
            return self.msg
        if isinstance(self.field, (list, tuple)):
            return "%s: %s" % (", ".join(self.field), self.msg)
        return "%s: %s" % (self.field, self.msg)

class Required(object):
    def __init__(self, field, strip=True, msg="Missing required value"):
        self.field = field
        self.strip = strip
        self.msg = msg

    def __call__(self, record, result):
        fld = self.field
        value = record.get(fld, '')
        if not isinstance(value, basestring):
            if not value:
                result.error(fld, self.msg)
            return
        if self.strip:
            value = value.strip()
        if not value:
            result.error(fld, self.msg)

class Values(object):
    def __init__(self, field, values, msg=None):
        self.field = field
        self.values = values

        assert values

        if msg is None:
            s = []
            if len(values) == 1:
                valstr = values[0]
            elif len(values) == 2:
                valstr = "%r or %r" % tuple(values)
            else:
                for i, v in enumerate(values):
                    if i == len(values) -1:
                        s.extend(["or", v])
                    else:
                        s.extend(["%r," % v])
                valstr = " ".join(s)
            self.msg = "Value must be %s not %%r" % valstr
        else:
            self.msg = msg

    def __call__(self, record, result):
        fld = self.field
        value = record.get(fld, '')
        if not value:
            return
        if value not in self.values:
            result.error(fld, self.msg % value)

class ISODate(object):
    def __init__(self, field, msg='Invalid date %s. Expected YYYYMMDD'):
        self.field = field
        self.msg = msg

    def __call__(self, record, result):
        fld = self.field
        value = record.get(fld, '')
        if not value:
            return

        try:
            time.strptime(value, "%Y%m%d")
        except ValueError:
            result.error(fld, self.msg % value)

class DateInPast(object):
    def __init__(self, field):
        self.field = field

    def __call__(self, record, result):
        value = record.get(self.field, '')
        if not value:
            return
        try:
            value = time.strptime(value, "%Y%m%d")
        except ValueError:
            return

        value = datetime.date(*value[:3])
        if value > datetime.date.today():
            result.error(self.field, "Value must be in the past.")

