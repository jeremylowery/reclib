from setuptools import setup

setup(
    name="reclib",
    version="2023.11.17",
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
