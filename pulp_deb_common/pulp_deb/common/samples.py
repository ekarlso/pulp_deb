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


def get_resource_data(rn):
    resource = REPO.copy()
    resource['component'] = resource.pop('component')[0]
    resource['arch'] = resource['arch'][0]
    resource['resource_name'] = rn
    return resource
