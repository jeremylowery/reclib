#!/usr/bin/env python
import os

from distutils.command.install_data import install_data, convert_path
from distutils.core import setup
from glob import glob

class my_install_data(install_data):
    """ Customization of install data. """
    def run(self):
        install_data.run(self)
        return
        #opj = os.path.join
        #res_dir = convert_path('srv/csweb/files')
        #res_dir = opj(self.install_dir, res_dir)
        #os.chmod(opj(res_dir, 'cblhttp_tunnel'), 0600)

def fglob(pat):
    return [f for f in glob(pat) if os.path.isfile(f)]

os.chdir(os.path.abspath(os.path.join(__file__, "..")))

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
    packages=['reclib']
)
