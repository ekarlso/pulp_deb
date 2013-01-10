import json
import os

from pulp_deb.common import model


DATA_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                         '..', '..', 'data')


def load(f):
    fh = open(os.path.join(DATA_PATH, 'fixtures', f + '.json'))
    json_str = fh.read()
    fh.close()
    return json.loads(json_str)


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


PACKAGES_URL = BASE_URL + '/dists/%(dist)s/%(component)s/binary-%(architecture)s/Packages.gz'
SOURCES_URL = BASE_URL + '/dists/%(dist)s/%(component)s/source/Sources.gz'
CONTENTS_URL = BASE_URL + '/dists/%(dist)s/Contents-%(architecture)s.gz'


def local_repo_location():
    return 'file://' + os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', '..', 'test', 'repos')


def dist(**kw):
    data = load('dist')
    data.update(kw)
    return model.Distribution(**data)


def component(**kw):
    data = load('component')
    data.update(kw)
    return model.Component(**data)


def package(**kw):
    data = load('package')
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
