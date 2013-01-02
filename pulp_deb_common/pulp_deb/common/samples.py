import os


BASE_URL = 'http://ubuntu.uib.no/archive'

DIST = 'precise'
COMPONENT = 'main'
ARCH = 'amd64'

REPO = dict(
    url=BASE_URL,
    dist=DIST,
    component=[COMPONENT],
    arch=[ARCH]
)


PACKAGES_URL = BASE_URL + '/dists/%(dist)s/%(component)s/binary-%(arch)s/Packages.gz'
SOURCES_URL = BASE_URL + '/dists/%(dist)s/%(component)s/source/Sources.gz'
CONTENTS_URL = BASE_URL + '/dists/%(dist)s/Contents-%(arch)s.gz'


def get_repo(**kw):
    repo = REPO.copy()
    repo.update(kw)
    return repo


def get_resource_data(rn, repo_kw={}, **kw):
    resource = get_repo(**repo_kw)
    resource['component'] = resource.pop('component')[0]
    resource['architecture'] = resource['architecture'][0]
    resource['resource_name'] = rn
    return resource


def local_repo_location():
    return 'file://' + os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', '..', 'test', 'repos')


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
