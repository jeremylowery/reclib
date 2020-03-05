import re
import six
from decimal import Decimal

from reclib.util import decimal2implicit, parse_decimal

class Currency(object):
    def __init__(self, name, length, **kw):
        self.name = name
        self.length = length
        self.implied_decimal = kw.get('implied_decimal', None)
        self.pad = kw.get('pad', ' ')
        assert len(self.pad) == 1, "Numeric pad character must be one byte"

    def format(self, record, reporter):
        value = record.get(self.name, '')
        if value in (None, ''):
            return self.pad * self.length
        if not isinstance(value, Decimal):
            value = parse_decimal(value)

        if self.implied_decimal is not None:
            value = decimal2implicit(value, self.implied_decimal)

        return str(value).rjust(self.length, self.pad)

class Integer(object):
    def __init__(self, name, length):
        self.name = name
        self.length = length

    def format(self, record, reporter):
        value = record.get(self.name, '')
        if value in (None, ''):
            return '0'*self.length
        return str(value).rjust(self.length, '0')

Numeric = Currency

class String(object):
    """ A string value
    length: how wide the fixed with field may be. Can also be a 2 tuple, which
            indicates the width and number of lines. The input is split on
            sep. The lines are then flattened, each line of the input 
            truncated to the width given.
    upper: uppercase the entire string
    lower: lowercase the entire string
    pad:   character to pad out the string with, by default ' ' but '0' may be
           useful as well.
    tr:    translation map. provide a mapping from found values to output
           values
    align: which side to align the text to inside of length, controls where
           white-space is added. if length is a tuple, each line is aligned.
    sep: only used when length is a tuple, determines the line separator.
         Defaults to "\r\n" because this feature was originally written for
         parsing web posts.
    """

    def __init__(self, name, length, **kw):
        self.name = name
        self.length = length
        self.align = kw.get('align', 'left')
        self.upper = kw.get('upper', False)
        self.lower = kw.get('lower', False)
        self.tr = kw.get('tr')
        self.truncate = kw.get('truncate', False)
        self.pad = kw.get('pad', ' ')

        # allows for boxed data
        self.sep = kw.get('sep', '\r\n')

    def format(self, record, reporter):
        value = record.get(self.name, '')
        if not isinstance(value, basestring):
            raise ValueError("%s value %r is not string" % (self.name, value))
        if isinstance(self.length, int) and len(value) > self.length:
            v = value[:self.length]
            if not self.truncate:
                reporter.warning("Truncating %s to %s" % (value, v))
            value = v
        if self.upper:
            value = value.upper()
        elif self.lower:
            value = value.lower()
        if self.tr:
            value = self.tr.get(value, value)

        if isinstance(self.length, int):
            return self.just(value, self.length)
        else:
            w, h = self.length
            lines = []
            data = value.split(self.sep)
            for i in range(h):
                try:
                    line = data[i]
                except IndexError:
                    line = ''
                line = self.just(line[:w], w)
                lines.append(line)
            return "".join(lines)

    def just(self, value, length):
        align_map = {
            'left' : value.ljust,
            'right' : value.rjust,
            'center' : value.center}
        return align_map[self.align](length, self.pad)


class Date(object):
    def __init__(self, name, length, fmt):
        self.length = length
        self.name = name
        self.fmt = fmt

    def format(self, record, reporter):
        value = record.get(self.name)
        if value is None:
            return ' ' * self.length
        else:
            try:
                return value.strftime(self.fmt).ljust(self.length)
            except ValueError:
                # year is before 1900
                return '?' * self.length

class Array(object):
    """ The value coming in will be expected to be a sequence."""
    def __init__(self, stype, count, sep=''):
        self.stype = stype
        self.name = self.stype.name
        self.count = count
        self.sep = sep

    def format(self, record, reporter):
        values = record.get(self.name, [])
        if len(values) > self.count:
            reporter.warn("Too many values given for %s. Only using the "
                      "first %s values of %r", self.name, self.count, values)

        value = []
        for i in range(self.count):
            try:
                rec = {self.name : values[i]}
            except IndexError:
                # So the formatter's default behavior can be used.
                rec = {}
            value.append(self.stype.format(rec, reporter))
        
        return self.sep.join(value)

class Formatter(object):
    fields = []

    def format(self, records, file_obj=None, reset=True):
        if file_obj is None:
            file_obj = six.StringIO()
        reporter = Reporter()
        for idx, record in enumerate(records):
            for field in self.fields:
                reporter.set_field(field, idx)
                value = field.format(record, reporter)
                file_obj.write(value)
            if idx != len(records) - 1:
                file_obj.write("\n")
        if reset:
            file_obj.seek(0)
        return file_obj

    def formatone(self, record, file_obj=None, reset=True):
        if file_obj is None:
            file_obj = six.StringIO()
        reporter = Reporter()
        for field in self.fields:
            reporter.set_field(field, 1)
            value = field.format(record, reporter)
            file_obj.write(value)
        if reset:
            file_obj.seek(0)
        return file_obj

    def format2file(self, records, path):
        f = open(path, 'w')
        self.format(record, f, False)
        f.close()

class Reporter(object):
    def __init__(self):
        self.warnings = []

    def set_field(self, field, record_num):
        self.field = field
        self.record_num = record_num

    def warning(self, msg, *args):
        if args: msg %= args
        self.warnings.append((self.field, self.record_num, msg))

