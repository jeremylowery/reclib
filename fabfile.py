import commands
import glob
import os
import re
import shutil

from fabric.api import *

#env.hosts = [']

def _get_version():
    return commands.getoutput(r'cat setup.py  | grep version | cut -d\" -f2')

def update():
    local("rm -rf /usr/local/lib/python2.6/dist-packages/reclib")
    local("python setup.py --quiet install --prefix=/usr/local")

def deploy(revision='tip'):
    """ Send off to production server and install """

    # Clean out working directory
    if os.path.exists("/tmp/reclib"):
        local("rm -rf /tmp/reclib")

    # Pull source code from remote repository
    # Pull out a clean version of the code to build from
    local("hg clone -qr %s . /tmp/reclib" % revision)

    # Build a source distribution
    with lcd("/tmp/reclib"):
        local("python setup.py -q sdist")

    # distutils creates the tarball with the version from setup.py in it. We
    # do not know that version here, so we have to parse it out of the tar ball
    # file name.
    flist = glob.glob('/tmp/reclib/dist/*.tar.gz')
    if len(flist) != 1:
        print 'Expected tarball in /tmp/reclib/dist. found %s' % ' '.join(flist)
        return

    tb_path = flist[0]
    tb_fname = os.path.basename(tb_path)
    # the app_dir is the directory that the tarball is going to place the files
    # in. This is the app name - version.
    app_dir = tb_fname[:tb_fname.find('.tar.gz')]

    # Send the source distribution to host
    put(tb_path, "/tmp")

    # untar the source distribution
    with cd("/tmp"):
        run("tar xzf %s" % tb_fname)

    # Install the source package on the host
    with cd("/tmp/%s" % app_dir):
        run("python setup.py -q install --prefix=/usr/local")
    # reload apache
    run("sudo apache2ctl graceful")
