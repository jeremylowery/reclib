#!/usr/bin/env python
import os
from distutils.core import setup

setup(
    name="reclib",
    version="2011.9.30",
    provides=["reclib"],
    description="reclib library",
    long_description="record parsing and validating library",
    license="",
    author="Jeremy Lowery",
    author_email="jeremy@bitrel.com",
    url="http://bitrel.com",
    platforms="POSIX",
    packages=['reclib', 'reclib.parse', 'reclib.format']
)
