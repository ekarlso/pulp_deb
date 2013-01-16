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


import base_downloader
from pulp_deb.plugins.importers.downloaders.exceptions import FileNotFoundException
from pulp_deb.plugins.importers.downloaders.local import LocalDownloader


class LocalDownloaderTests(base_downloader.BaseDownloaderTests):

    def setUp(self):
        super(LocalDownloaderTests, self).setUp()
        self.downloader = LocalDownloader(self.repo, None, self.config, self.mock_cancelled_callback)

    def test_download_resource(self):
        # Setup
        indexes = self.dist.get_indexes()

        # Test
        self.downloader.download_resources(indexes, self.mock_progress_report)

        # Verify
        self.assertEqual(3, len(indexes))

        self.assertEqual(3, self.mock_progress_report.query_total_count)
        self.assertEqual(3, self.mock_progress_report.query_finished_count)
        self.assertEqual(2, self.mock_progress_report.update_progress.call_count)

    def test_download_resource_not_found(self):
        # Setup
        indexes = self.dist.get_indexes()
        indexes[1]['url'] = indexes[1]['url'] + '_'

        # Test & Verify
        try:
            self.downloader.download_resources(indexes, self.mock_progress_report)
            self.fail()
        except FileNotFoundException, e:
            self.assertEqual(e.location in [r['url'] for r in indexes], True)

    def test_download_in_memory_as_list(self):
        resources = self.dist.get_indexes()

        self.downloader.download_resources(
            resources, self.mock_progress_report, in_memory=True)

        # Verify
        self.assertEqual(3, len(resources))

        for resource in resources:
            self.assertEqual(type(resource['content']), list)
            self.assertEqual(len(resource['content']) > 1, True)
