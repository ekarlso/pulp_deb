import os
from pulp_deb.common import model


BASE_URL = 'http://ubuntu.uib.no/archive'
DIST_NAME = 'precise'
COMPONENT_NAME = 'main'
ARCH_NAMES = ['amd64', 'i686']

COMPONENT = dict(
    name=COMPONENT_NAME,
    arch=ARCH_NAMES)

DIST = dict(
    name=DIST_NAME,
    components=[COMPONENT])

PKG_DATA = {
  "SHA256": u"6081ce4e689934a0de2ff9525c11e35b604d2b1b695dcad3cf12e95830611be8",
  "Maintainer": u"Ubuntu Developers <ubuntu-devel-discuss@lists.ubuntu.com>",
  "Description": u"lightweight C library for daemons - runtime library\n libdaemon is a leightweight C library which eases the writing of UNIX daemons.\n It consists of the following parts:\n .\n  * Wrapper around fork() for correct daemonization of a process\n  * Wrapper around syslog() for simple log output to syslog or STDERR\n  * An API for writing PID files\n  * An API for serializing signals into a pipe for use with select() or poll()\n  * An API for running subprocesses with STDOUT and STDERR redirected to syslog\n .\n Routines like these are included in most of the daemon software available. It\n is not simple to get these done right and code duplication is not acceptable.\n .\n This package includes the libdaemon run time shared library.",
  "SHA1": u"6d10e81457f7dcd9c2c48fce797662246d8de947",
  "Package": u"libdaemon0",
  "Section": u"libs",
  "MD5sum": u"c714e7fec80be42a0d4b54ab88c2c08a",
  "Depends": u"libc6 (>= 2.8)",
  "Filename": u"pool/main/libd/libdaemon/libdaemon0_0.14-2_amd64.deb",
  "Priority": u"optional",
  "Source": u"libdaemon",
  "Installed-Size": u"84",
  "Version": u"0.14-2",
  "Architecture": u"amd64",
  "Size": u"18916",
  "Homepage": u"http://0pointer.de/lennart/projects/libdaemon/",
  "Original-Maintainer": u"Utopia Maintenance Team <pkg-utopia-maintainers@lists.alioth.debian.org>"
}

PACKAGES_URL = BASE_URL + '/dists/%(dist)s/%(component)s/binary-%(architecture)s/Packages.gz'
SOURCES_URL = BASE_URL + '/dists/%(dist)s/%(component)s/source/Sources.gz'
CONTENTS_URL = BASE_URL + '/dists/%(dist)s/Contents-%(architecture)s.gz'


def local_repo_location():
    return 'file://' + os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', '..', 'test', 'repos')


def dist(**kw):
    data = DIST.copy()
    data.update(kw)
    return model.Distribution(**data)


def component(**kw):
    data = COMPONENT.copy()
    data.update(kw)
    return model.Component(**data)


def package(**kw):
    data = PKG_DATA.copy()
    data.update(kw)
    return model.Package(**data)


def valid_repo(**kw):
    if 'url' not in kw:
        kw['url'] = local_repo_location() + '/valid'
    repo = get_repo(**kw)
    return repo


def invalid_repo(**kw):
    if 'url' not in kw:
        kw['url'] = local_repo_location() + '/invalid'
    repo = get_repo(**kw)
    return repo
