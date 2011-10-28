""" Object system for parsing fixed width data. Includes validation 
options and format specification.

Not meant for complex multi field logic or business rules processing. Need to
have a general validation object system for that.
"""
import cStringIO
import csv
import datetime
import decimal
import os
import re
import time

import rec

from reclib.util import strftime

class Parser(object):
    """ The parser builds a set of records from a file, stream or path.
    It provides a clean interface to clients. """
    fields = []
    spacing = 0
    
    file_name = None

    def __init__(self, *fields):
        if fields:
            self.fields = fields

    def parse(self, file_obj, src=None):
        stream = RecordStream(file_obj)
        records = rec.RecordSet(src)
        while not stream.eof:
            record = self.parseline(stream)
            if not stream.eof:
                records.append(record)
        return records

    def parseline(self, stream):
        # Possible that a file object was passed in
        if not isinstance(stream, RecordStream):
            stream = RecordStream(stream)
        record = Record(self.fields, self.spacing)
        record.parse(stream)
        while not stream.eof and stream.read(1) != '\n':
            pass
        return record

    def parse_file(self, path=None):
        if path is not None:
            self.file_name = path
        file_obj = open(self.file_name)
        records = self.parse(file_obj, os.path.basename(self.file_name))
        file_obj.close()
        return records

    def parse_iter(self, file=None):
        if file is None:
            file_obj, src = open(self.file_name), self.file_name
        elif isinstance(file, basestring):
            file_obj, src = open(file), file
        else:
            file_obj, src = file, None
        stream = RecordStream(file_obj)
        records = rec.RecordSet(src)
        while not stream.eof:
            record = self.parseline(stream)
            if not stream.eof:
                yield record

class RecordStream(object):
    """
    Utility
    
    This record stream encapsulates a file, along with its line count,
    and positions in the file.

    XXX:TODO Implement readline(s)
    """
    def __init__(self, file_obj):
        self.file_obj = file_obj
        self.line_no = 1
        self.eof = False
        self.dead_read = False
        self.cur_line_pos = 0

    def read(self, size):
        bytes = self.file_obj.read(size)
        nlp = bytes.find('\n')
        if nlp != -1:
            self.cur_line_pos = self.file_obj.tell() - len(bytes) + nlp + 1
            self.line_no += 1
        if len(bytes) < size:
            self.eof = True
            if len(bytes) == 0:
                self.dead_read = True
        return bytes

    def get_pos(self):
        """ return the line character the file is positioned at """
        return self.file_obj.tell() - self.cur_line_pos

    def __getattr__(self, attr):
        return getattr(self.file_obj, attr)

class Record(dict):
    def __init__(self, fields, spacing):
        self.fields = fields
        self.spacing = spacing
        self.errors = rec.RecordErrorSet()
        self.warnings = rec.RecordWarningSet()

    def parse(self, stream):
        self.line_no = stream.line_no

        for field in self.fields:
            self[field.name] = None

        for j, field in enumerate(self.fields):
            pos = stream.get_pos()
            err = lambda m, v=None: self.errors(field, v, m, pos)
            warn = lambda m, v=None: self.warnings(field, v, m, pos)
            field.assign(self, stream, err, warn)
            if stream.eof:
                return

            # We don't read spacing on the last record
            if j != (len(self.fields)-1) and self.spacing:
                stream.read(self.spacing)

    def format(self):
        pad = max(len(v) for v in self)
        return "\n".join("%s: %r" % (k.ljust(pad), self[k]) for k in self)

    def format_errors(self):
        return "line: %05d\n%s\n-----\n" % (self.line_no, self.errors.format())

class Multi(object):
    """ Multi-value field. Appends the value of the given in a list."""
    def __init__(self, stype, count, join=None, rstrip=False):
        self.stype = stype
        self.name = self.stype.name
        self.count = count
        self.join = join
        self.rstrip = rstrip

    def parse(self, stream, err, warn):
        values = {}

        for i in range(self.count):
            record = {}
            self.stype.assign(record, stream, err, warn)
            for k, v in record.items():
                values.setdefault(k, [])
                values[k].append(v)
            if stream.eof:
                break

        if self.join is not None:
            jval = {}
            for k, v in values.items():
                jval[k] = self.join.join(v)
                if self.rstrip:
                    jval[k] = jval[k].rstrip()

            values = jval

        return values

    def assign(self, record, stream, err, warn):
        for k, v in self.parse(stream, err, warn).items():
            record[k] = v

class RecordList(object):
    """ A list of sub-records in a main record. Similar to Multi, but parses
    in a different order.
    """
    def __init__(self, name, count, *fields):
        self.name = name
        self.count = count
        self.fields = fields
        self.spacing = 0

    def parse(self, stream, err, warn):
        records = []
        for i in range(self.count):
            record = Record(self.fields, self.spacing)
            record.parse(stream)
            if stream.eof:
                break
            else:
                records.append(record)
        return records

    def assign(self, record, stream, err, warn):
        record[self.name] = self.parse(stream, err, warn)

class String(object):
    def __init__(self, name, length, **kw):
        self.name = name
        self.length = length
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
        self.regex_sub = kw.get("regex_sub")
        self.regex_replace = kw.get("regex_replace", "")

    def parse(self, stream, err, warn):
        if self.length == 0:
            return ''
        value = stream.read(self.length)
        # Manage white space
        if self.strip_left:
            value = value.lstrip()
        if self.strip_right:
            value = value.rstrip()

        # Validate
        if self.required and value == "":
            err("missing required value", value)
            return

        if value != "" or self.validate_blank:
            if self.regex and not re.match(self.regex, value):
                err("does not match pattern %s" % self.regex, value)
            if self.values and value not in self.values:
                err("unexpected value", value)

        # Transform
        if self.regex_sub:
            value = re.sub(self.regex_sub, self.regex_replace, value)

        if self.tr:
            try:
                value = self.tr[value]
            except KeyError:
                if self.tr_match:
                    err("unexpected value", value)
        if self.title:
            value = value.title()
        if self.upper:
            value = value.upper()
        if self.lower:
            value = value.lower()
        return value

    def assign(self, record, stream, err, warn):
        record[self.name] = self.parse(stream, err, warn)
        
class Date(object):
    zero_pat = re.compile('^0+$')

    def __init__(self, name, length, format='%m/%d/%Y', 
                 required=False, 
                 val_format=None,
                 none_if_invalid=False,
                 min_year=None):
        self.name = name
        self.length = length
        self.format = format
        self.required = required
        self.none_if_invalid = none_if_invalid
        self.val_format = val_format
        self.min_year = min_year

    def parse(self, stream, err, warn):
        if self.length == 0:
            return
        value = stream.read(self.length).strip()
        if self.zero_pat.match(value):
            value = ''
        if not value:
            if self.required:
                err("missing required value", value)
            return
        else:
            try:
                value = time.strptime(value, self.format)
                value = datetime.date(*(value[:3]))
            except ValueError:
                if not self.none_if_invalid:
                    err("invalid date, expected format %r" % self.format, value)
                return
        if self.min_year and value.year < self.min_year:
            err("Expected year after %s" % self.min_year, value)
            return
        if self.val_format:
            try:
                value = strftime(value, self.val_format)
            except AttributeError:
                value = ''
        return value

    def assign(self, record, stream, err, warn):
        field = self.name
        record[field] = self.parse(stream, err, warn)
        if record[field] and isinstance(record[field], datetime.date):
                record["%s_fmt" % field] = strftime(record[field], "%m/%d/%Y")
                record["%s_iso" % field] = strftime(record[field], "%Y%m%d")
        else:
            record["%s_fmt" % field] = ""
            record["%s_iso" % field] = ""

class Datetime(object):
    formats = {
        'YYYYMMDD' : (8, '%Y%m%d'),
        'YYMMDD'   : (6, '%y%m%d'),
        'MMDDYYYY' : (8, '%m%d%Y'),
        'YYYYMMDDHHMMSS' : (14, '%Y%m%d%H%M%S')
    }
    def __init__(self, name, format='YYYYMMDDHHMMSS', 
                 required=False, 
                 val_format=None,
                 none_if_invalid=False,
                 min_year=None):
        self.name = name
        self.length, self.format = self.formats[format]
        self.required = required
        self.none_if_invalid = none_if_invalid
        self.val_format = val_format
        self.min_year = min_year

    def parse(self, stream, err, warn):
        if self.length == 0:
            return
        value = stream.read(self.length).strip()
        if not value:
            if self.required:
                err("missing required value", value)
                return
            else:
                value = None
        else:
            try:
                value = time.strptime(value, self.format)
                value = datetime.datetime(*(value[:6]))
            except ValueError:
                if not self.none_if_invalid:
                    err("invalid datetime, expected format %r" % self.format,
                        value)
                return
        if self.min_year and value.year < self.min_year:
            err("Expected year after %s" % self.min_year, value)
            return
        if self.val_format:
            try:
                value = strftime(value, self.val_format)
            except AttributeError:
                value = ''
        return value

    def assign(self, record, stream, err, warn):
        field = self.name
        record[field] = self.parse(stream, err, warn)
        if record[field] and isinstance(record[field], datetime.date):
            record["%s_fmt" % field] = strftime(record[field], "%x %X")
            record["%s_iso" % field] = strftime(record[field], "%Y%m%d %H:%M")
        else:
            record["%s_fmt" % field] = ""
            record["%s_iso" % field] = ""



class Currency(object):
    def __init__(self, name, length, required=False, nonzero=False, 
                 implicit=None):
        self.name = name
        self.length = length
        self.required = required
        self.nonzero = nonzero
        if implicit:
            self.implicit = decimal.Decimal(implicit)
        else:
            self.implicit = None

    def parse(self, stream, err, warn):
        if self.length == 0:
            return
        value = stream.read(self.length).strip()
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
                err(str(e), value)
                return

        if self.nonzero and value == 0:
            err("value cannot be zero", value)
            return

        if self.implicit:
            value = value / (10 ** self.implicit)
        return value

    def assign(self, record, stream, err, warn):
        record[self.name] = self.parse(stream, err, warn)

Numeric = Currency

class Integer(object):
    sexp = re.compile("[^\d]")
    def __init__(self, name, length, required=False, strip_nonnumeric=True):
        self.name = name
        self.length = length
        self.required = required
        self.strip_nonnumeric = strip_nonnumeric

    def parse(self, stream, err, warn):
        if self.length == 0:
            return
        value = stream.read(self.length).strip()
        if self.strip_nonnumeric:
            value = self.sexp.sub("", value)
        try:
            value = int(value)
        except ValueError:
            err("cannot translate to number", value)
            return
        return value

    def assign(self, record, stream, err, warn):
        record[self.name] = self.parse(stream, err, warn)

