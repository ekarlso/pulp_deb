import unittest

from pulp_deb.common import constants
from pulp_deb.common import samples
from pulp_deb.plugins.importers.downloaders import url_utils


class URLTests(unittest.TestCase):
    def test_get_contents_url(self):
        data = samples.get_resource_data('contents')

        url = url_utils.get_resource_url(data)
        self.assertEquals(url, samples.CONTENTS_URL % data)

    def test_get_packages_url(self):
        data = samples.get_resource_data('packages')

        url = url_utils.get_resource_url(data)
        self.assertEquals(url, samples.PACKAGES_URL % data)

    def test_get_sources_url(self):
        data = samples.get_resource_data('sources')

        url = url_utils.get_resource_url(data)
        self.assertEquals(url, samples.SOURCES_URL % data)

    def test_get_url_missing_info(self):
        data = samples.get_resource_data('packages')
        del data['arch']

        for resource in constants.RESOURCES:
            self.assertRaises(KeyError, url_utils.get_resource_url, data)
