import json
import os

from pulp_deb.common import model


DATA_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                         '..', '..', 'data')


def read(f):
    fh = open(os.path.join(DATA_PATH, 'fixtures', f + '.json'))
    fc = fh.read()
    fh.close()
    return fc


def load(f):
    json_str = read(f)
    return json.loads(json_str)


DIST = load('dist')
COMPONENT = load('component')
PACKAGE = load('package')


BASE_URL = 'http://ubuntu.uib.no/archive'


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
