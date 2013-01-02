import logging
import urlparse

from pulp_deb.common import constants
from pulp_deb.plugins.importers.downloaders.exceptions import UnsupportedURLType, InvalidURL


LOG = logging.getLogger(__name__)


def get_url_dict(resource, url, dist, component=None, architecture=None):
    """
    Return a dict with the necassary data to create a URL
    """
    data = {
        'resource_name': resource,
        constants.CONFIG_URL: url,
        constants.CONFIG_DIST: dist,
        constants.CONFIG_COMPONENT: component}

    if architecture is not None:
        data[constants.CONFIG_ARCH] = architecture

    return data


def get_resource_url(resource):
    return constants.URLS.get(resource['resource_name']) % resource


def get_resources(config):
    """
    Get a list containing dicts with the data used + the url for the given resource
    """
    repo = get_repo(config)

    resources = []

    def _resource(*args, **kw):
        resource = get_url_dict(*args, **kw)
        resource['resource'] = get_resource_url(resource)
        resources.append(resource)

    for architecture in repo['architecture']:
        for cmpt in repo['component']:
            for resource in constants.RESOURCES:
                _resource(resource, repo['url'], repo['dist'], cmpt, architecture=architecture)
    return resources


def get_repo(config):
    return dict([(k, config.get(k)) for k in constants.CONFIG_REPO])


def determine_url_type(url):
    """
    Returns the type of url represented by the given url.

    :param url: url being synchronized
    :type  url: str

    :return: type to use to retrieve the downloader instance
    :rtype:  str

    :raise InvalidURL: if the url is invalid and a url cannot be
           determined
    """
    try:
        proto, netloc, path, params, query, frag = urlparse.urlparse(url)
        return proto
    except Exception:
        LOG.exception('Exception parsing url type for url <%s>' % url)
        raise InvalidURL(url)
