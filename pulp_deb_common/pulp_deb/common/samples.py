import json
import os

from pulp_deb.common import constants, model


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


MODELS = {
    constants.CONFIG_DIST: model.Distribution,
    constants.CONFIG_COMPONENT: model.Component,
    'package': model.Package}


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


def get_repo(path='valid', load_model=True, **kw):
    if 'url' not in kw:
        kw['url'] = os.path.join(local_repo_location(), path)
    return get_model('dist', **kw) if load_model else get_data('dist', **kw)


def get_valid_repo(**kw):
    return get_repo(**kw)


def get_invalid_repo(**kw):
    return get_repo(path='invalid', **kw)
