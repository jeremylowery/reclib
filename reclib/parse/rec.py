class RecordSet(list):
    def __init__(self, src=None):
        self.src = src

    _idx = 0
    def __iter__(self):
        self._idx = 0
        return self

    def next(self):
        try:
            v = self[self._idx]
        except IndexError:
            raise StopIteration()
        self._idx += 1
        return v

    @property
    def error_size(self):
        return len([x for x in self if x.errors])

    @property
    def error_count(self):
        return sum(len(x.errors) for x in self)

    def accepted(self):
        x = RecordSet(self.src)
        x.extend([r for r in self if not r.errors])
        return x

    def rejected(self):
        x = RecordSet(self.src)
        x.extend([r for r in self if r.errors])
        return x

class RecordErrorSet(list):
    def __call__(self, field, value, msg, col=None):
        self.append((field, value, msg, col))

    def format(self, sep="\n"):
        return sep.join(self.format_item(i) for i in self)

    def format_item(self, item):
        field, value, msg, col = item
        if col:
            return "[%s] %s=%r: %s" % (col, field.name, value, msg)
        else:
            return "%s=%r: %s" % (field.name, value, msg)

class RecordWarningSet(list):
    def __call__(self, field, value, msg, col=None):
        self.append((field, value, msg, col))

    def format(self, sep="\n"):
        return sep.join(self.format_item(i) for i in self)

    def format_item(self, item):
        field, value, msg, col = item
        if col:
            return "[%s] %s=%r: %s" % (col, field.name, value, msg)
        else:
            return "%s=%r: %s" % (field.name, value, msg)


