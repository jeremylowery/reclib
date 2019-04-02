import cStringIO
import csv
import datetime
import decimal
import logging
import os
import re
import rec
import time

log = logging.getLogger('reclib')

class Parser(object):
    fields = []
    header_lines = 0
    _field_cache = None
    delimiter = ','
    dialect=csv.excel

    def parse(self, file_obj, src=None):
        records = rec.RecordSet(src)
        r = csv.reader(file_obj, delimiter=self.delimiter,
                       dialect=self.dialect)
        for i, line in enumerate(r):
            if i < self.header_lines:
                continue
            line_no = i + 1
            record = Record(self.fields, line, line_no)
            record.parse()
            self.post_process(record)
            records.append(record)
        return records

    def post_process(self, record):
        pass

    def field(self, name):
        if not self._field_cache:
            self._field_cache = dict((f.name, f) for f in self.fields)
        return self._field_cache[name]
            
    def parse_file(self, path):
        file_obj = open(path)
        records = self.parse(file_obj, os.path.basename(path))
        file_obj.close()
        return records

class Record(dict):
    def __init__(self, fields, src, line_no):
        self.fields = fields
        self.src = src
        self.line_no = line_no
        self.errors = rec.RecordErrorSet()
        self.warnings = rec.RecordWarningSet()

        while len(self.src) < len(self.fields):
            self.src.append('')

    def parse(self):
        for value, field in zip(self.src, self.fields):
            err = lambda m: self.errors(field, value, m)
            warn = lambda m: self.warnings(field, value, m)
            value = field.parse(value, err, warn)
            self[field.name] = value

class Currency(object):
    def __init__(self, name, required=False, nonzero=False):
        self.name = name
        self.required = required
        self.nonzero = nonzero

    def parse(self, value, err, warn):
        value = value.strip()
        if not value:
            if self.required:
                err("missing required value")
                return
            else:
                value = decimal.Decimal("0")
        else:
            try:
                value = decimal.Decimal(value)
            except Exception, e:
                err(str(e))
                return

        if self.nonzero and value == 0:
            err("value cannot be zero")
            return
        return value

class Integer(object):
    sexp = re.compile("[^\d]")
    def __init__(self, name, required=False, strip_nonnumeric=True):
        self.name = name
        self.required = required
        self.strip_nonnumeric = strip_nonnumeric

    def parse(self, value, err, warn):
        value = value.strip()
        if self.strip_nonnumeric:
            value = self.sexp.sub("", value)
        try:
            value = int(value)
        except ValueError:
            err("cannot translate to number")
            return
        return value

class String(object):
    def __init__(self, name, **kw):
        self.name = name
        self.values = kw.get('values')
        self.regex = kw.get('regex')
        self.strip_left = kw.get('strip_left', False)
        self.strip_right = kw.get('strip_right', True)
        self.required = kw.get('required', False)
        self.validate_blank = kw.get('validate_blank', False)
        self.title = kw.get('title', False)
        self.upper = kw.get('upper', False)
        self.lower = kw.get('lower', False)
        self.tr = kw.get('tr', False)
        self.tr_match = kw.get('tr_match', True)

    def parse(self, value, err, warn):
        # Manage white space
        if self.strip_left:
            value = value.lstrip()
        if self.strip_right:
            value = value.rstrip()

        # Validate
        self.errors = []
        if self.required and value == "":
            err("missing required value")
            return

        if (value != "" or self.validate_blank):
            if self.regex and not re.match(self.regex, value):
                err("does not match pattern %s" % self.regex)
            if self.values and value not in self.values:
                err("unexpected value")

        # Transform
        if self.tr:
            try:
                value = self.tr[value]
            except KeyError:
                if self.tr_match:
                    err("unexpected value")
        if self.title:
            value = value.title()
        if self.upper:
            value = value.upper()
        if self.lower:
            value = value.lower()
        return value

class Date(object):
    def __init__(self, name, format='%m%d%Y', 
                 required=False, 
                 strip_spaces=True,
                 min_year=None):
        self.name = name
        self.format = format
        self.required = required
        self.strip_spaces = strip_spaces
        self.min_year = min_year

    def parse(self, value, err, warn):
        if self.strip_spaces:
            value = value.strip()
        if not value:
            if self.required:
                err("missing required value")
            return
        else:
            try:
                value = time.strptime(value, self.format)
                value = datetime.date(*(value[:3]))
            except ValueError:
                err("invalid date, expected format %r" % self.format)
                return
        if self.min_year and value.year < self.min_year:
            err("Expected year after %s" % self.min_year)
            return
        return value

