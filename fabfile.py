from fabric.api import *

os.chdir(os.path.dirname(__file__))

version = "0.2.0"
wheel = "reclib-{0}-py3-none-any.whl".format(version)

def build():
    local("python3 -m build")

def twine():
    local("twine upload dist/{0}".format(wheel))

def develop():
    local("python3 -m pip -e .")
