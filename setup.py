from setuptools import setup

setup(
    name="reclib",
    version="0.2.0",
    provides=["reclib"],
    description="reclib library",
    long_description="record parsing and validating library",
    license="",
    install_requires=[
        "future"
    ],
    author="Jeremy Lowery",
    author_email="jeremy@bitrel.com",
    url="http://bitrel.com",
    platforms="POSIX",
    packages=['reclib', 'reclib.parse', 'reclib.format']
)
