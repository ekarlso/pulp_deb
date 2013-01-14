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


MODELS = dict(
    dist=model.Distribution,
    component=model.Component,
    package=model.Package)


DATA = {}
for k in MODELS.keys():
    DATA[k] = load(k)


def get_data(name, **kw):
    d = DATA[name].copy()
    d.update(**kw)
    return d


def get_model(name, **kw):
    data = get_data(name, **kw)
    return MODELS[name](**data)


BASE_URL = 'http://ubuntu.uib.no/archive'


PACKAGES_URL = BASE_URL + '/dists/%(dist)s/%(component)s/binary-%(arch)s/Packages.gz'
SOURCES_URL = BASE_URL + '/dists/%(dist)s/%(component)s/source/Sources.gz'
CONTENTS_URL = BASE_URL + '/dists/%(dist)s/Contents-%(arch)s.gz'


def local_repo_location():
    return 'file://' + os.path.join(DATA_PATH, 'repos')


def repo(path='valid', **kw):
    if 'url' not in kw:
        kw['url'] = os.path.join(local_repo_location(), path)
    repo = get_model('dist', **kw)
    return repo


def valid_repo(**kw):
    return repo(**kw)


def invalid_repo(**kw):
    return repo(path='invalid', **kw)
