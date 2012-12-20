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

from pulp_deb.plugins.importers.downloaders import factory
from pulp_deb.plugins.importers.downloaders.exceptions import  UnsupportedURLType, InvalidURL
from pulp_deb.plugins.importers.downloaders.local import LocalDownloader


class DownloadersFactoryTests(unittest.TestCase):
    def test_is_valid_url(self):
        self.assertTrue(factory.is_valid_url('file://localhost'))

    def test_is_valid_url_false(self):
        self.assertFalse(factory.is_valid_url(None))

    def test_get_downloader(self):
        # Test
        downloader = factory.get_downloader('file://localhost', None, None, None, None)

        # Verify
        self.assertTrue(downloader is not None)
        self.assertTrue(isinstance(downloader, LocalDownloader))

    def test_get_downloader_invalid_url(self):
        try:
            factory.get_downloader(None, None, None, None, None)
            self.fail()
        except InvalidURL, e:
            self.assertEqual(e.url, None)

    def test_get_downloader_unsupported_url_type(self):
        try:
            factory.get_downloader('jdob://localhost', None, None, None, None)
            self.fail()
        except UnsupportedURLType, e:
            self.assertEqual(e.url_type, 'jdob')
