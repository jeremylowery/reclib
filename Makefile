export VERSION = 0.2.3
VENV ?= .venv
PY = $(VENV)/bin/python
PYFILES=$(shell find reclib -type f -name '*.py') setup.py
BUMPVER = $(VENV)/bin/bumpver
TWINE = $(VENV)/bin/twine
WHEEL = dist/reclib-$(VERSION)-py3-none-any.whl
TARBALL = dist/reclib-$(VERSION).tar.gz

.PHONY = all clean patch twine

all: $(WHEEL)

clean:
	rm -f $(TARBALL) $(WHEEL)

$(VENV):
	uv venv $(VENV)
	VIRTUALENV=$(VENV) uv pip install build
$(PY): $(VENV)

$(BUMPVER): $(VENV)
	VIRTUALENV=$(VENV) uv pip install bumpver

patch: $(BUMPVER)
	$(BUMPVER) update -p --commit

$(WHEEL): $(PY)
	$(PY) -m build

$(TWINE):
	VIRTUALENV=$(VENV) uv pip install twine

twine: $(TWINE) $(VENV) $(WHEEL)
	$(TWINE) upload $(WHEEL) $(TARBALL)

