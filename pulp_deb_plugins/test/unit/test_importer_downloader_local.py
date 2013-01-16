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
from pulp_deb.plugins.importers.downloaders import url_utils


def resource_urls(config):
    return [r['resource'] for r in url_utils.get_resources(config)]


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

        self.dist.update_from_resources([i for i in indexes])
        self.assertEqual(3, len(self.dist.packages))

        self.assertEqual(3, self.mock_progress_report.query_total_count)
        self.assertEqual(3, self.mock_progress_report.query_finished_count)
        self.assertEqual(2, self.mock_progress_report.update_progress.call_count)

    def test_download_resource_not_found(self):
        # Setup
        indexes = self.dist.get_indexes()
        indexes[1]['source'] = indexes[1]['source'] + '_'

        # Test & Verify
        try:
            self.downloader.download_resources(indexes, self.mock_progress_report)
            self.fail()
        except FileNotFoundException, e:
            self.assertEqual(e.location in [r['source'] for r in indexes], True)
