# -*- coding: utf-8 -*-
#
# Copyright © 2012 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public
# License as published by the Free Software Foundation; either version
# 2 of the License (GPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied,
# including the implied warranties of MERCHANTABILITY,
# NON-INFRINGEMENT, or FITNESS FOR A PARTICULAR PURPOSE. You should
# have received a copy of GPLv2 along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.


import unittest

import mock
from pulp.plugins.config import PluginCallConfiguration

from pulp_deb.common import constants
from pulp_deb.plugins.importers import configuration


REPO = dict(
    url='http://ubuntu.uib.no/archive',
    dist='precise',
    component=['main'],
    arch=['amd64']
)


def get_resource_data(rn):
    resource = REPO.copy()
    resource['component'] = resource.pop('component')[0]
    resource['arch'] = resource['arch'][0]
    resource['resource_name'] = rn
    return resource


BASE_URL = 'http://ubuntu.uib.no/archive'

PACKAGES_URL = BASE_URL + '/dists/precise/main/binary-amd64/Packages.gz'

SOURCES_URL = BASE_URL + '/dists/precise/main/source/Sources.gz'

CONTENTS_URL = BASE_URL + '/dists/precise/Contents-amd64.gz'


class URLTests(unittest.TestCase):
    def test_get_contents_url(self):
        data = get_resource_data('contents')

        url = configuration.get_resource_url(data)
        self.assertEquals(url, CONTENTS_URL)

    def test_get_packages_url(self):
        data = get_resource_data('packages')

        url = configuration.get_resource_url(data)
        self.assertEquals(url, PACKAGES_URL)

    def test_get_sources_url(self):
        data = get_resource_data('sources')

        url = configuration.get_resource_url(data)
        self.assertEquals(url, SOURCES_URL)

    def test_get_url_missing_info(self):
        data = get_resource_data('packages')
        del data['arch']

        for resource in configuration.RESOURCES:
            self.assertRaises(KeyError, configuration.get_resource_url, data)


class ResourcesTests(unittest.TestCase):
    def test_validate_resources(self):
        data = REPO.copy()
        config = PluginCallConfiguration(data, {})
        result, msg = configuration._validate_resources(config)

        self.assertTrue(result)
        self.assertTrue(msg is None)

    def test_validate_resources_missing_option(self):
        data = REPO.copy()
        del data['url']

        config = PluginCallConfiguration(data, {})
        result, msg = configuration._validate_resources(config)

        self.assertTrue(result)
        self.assertTrue(msg is None)

    def test_validate_resources_invalid(self):
        data = REPO.copy()
        del data['arch']

        config = PluginCallConfiguration(data, {})
        result, msg = configuration._validate_resources(config)

        self.assertTrue(not result)
        self.assertTrue(msg is not None)
        self.assertTrue('Resources error' in msg)


class RemoveMissingTests(unittest.TestCase):
    def test_validate_remove_missing(self):
        # Test
        config = PluginCallConfiguration({constants.CONFIG_REMOVE_MISSING: 'true'}, {})
        result, msg = configuration._validate_remove_missing(config)

        # Verify
        self.assertTrue(result)
        self.assertTrue(msg is None)

    def test_validate_remove_missing_missing(self):
        # Test
        config = PluginCallConfiguration({}, {})
        result, msg = configuration._validate_remove_missing(config)

        # Verify
        self.assertTrue(result)
        self.assertTrue(msg is None)

    def test_validate_remove_missing_invalid(self):
        # Test
        config = PluginCallConfiguration({constants.CONFIG_REMOVE_MISSING: 'foo'}, {})
        result, msg = configuration._validate_remove_missing(config)

        # Verify
        self.assertTrue(not result)
        self.assertTrue(msg is not None)
        self.assertTrue(constants.CONFIG_REMOVE_MISSING in msg)


class FullValidationTests(unittest.TestCase):

    @mock.patch('pulp_deb.plugins.importers.configuration._validate_resources')
    @mock.patch('pulp_deb.plugins.importers.configuration._validate_queries')
    @mock.patch('pulp_deb.plugins.importers.configuration._validate_remove_missing')
    def test_validate(self, missing, queries, resources):
        """
        Tests that the validate() call aggregates to all of the specific test
        calls.
        """
        # Setup
        all_mock_calls = (resources, missing, queries)

        for x in all_mock_calls:
            x.return_value = True, None

        # Test
        c = PluginCallConfiguration({}, {})
        result, msg = configuration.validate(c)

        # Verify
        self.assertTrue(result)
        self.assertTrue(msg is None)

        for x in all_mock_calls:
            x.assert_called_once_with(c)

    @mock.patch('pulp_deb.plugins.importers.configuration._validate_resources')
    @mock.patch('pulp_deb.plugins.importers.configuration._validate_queries')
    @mock.patch('pulp_deb.plugins.importers.configuration._validate_remove_missing')
    def test_validate_with_failure(self, missing, queries, resources):
        """
        Tests that the validate() call aggregates to all of the specific test
        calls.
        """
        # Setup
        all_mock_calls = (resources, missing, queries)

        for x in all_mock_calls:
            x.return_value = True, None
        all_mock_calls[1].return_value = False, 'foo'

        # Test
        c = {}
        result, msg = configuration.validate(c)

        # Verify
        self.assertTrue(not result)
        self.assertEqual(msg, 'foo')

        all_mock_calls[0].assert_called_once_with(c)
        all_mock_calls[1].assert_called_once_with(c)
        self.assertEqual(0, all_mock_calls[2].call_count)
