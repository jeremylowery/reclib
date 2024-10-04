from setuptools import setup

setup(
    name="reclib",
    version="0.2.2",
    provides=["reclib"],
    description="reclib library",
    long_description="record parsing and validating library",
    license="",
    install_requires=["future; python_version == '2.7'"],
    author="Jeremy Lowery",
    author_email="jeremy@bitrel.com",
    url="http://bitrel.com",
    platforms="POSIX",
    packages=["reclib", "reclib.parse", "reclib.format"],
)
