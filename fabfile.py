from fabric.api import *

version = "0.2.2"
wheel = "reclib-{0}-py3-none-any.whl".format(version)
tarball = "reclib-{0}.tar.gz".format(version)

def build():
    local("python3 -m build")

def bumpver():
    local("bumpver update -p --commit")

def twine():
    local("twine upload dist/{0} dist/{1}".format(wheel, tarball))

def develop():
    local("python3 -m pip -e .")
