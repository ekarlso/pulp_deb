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


import os

import base_downloader
from pulp_deb.common import constants, model, samples
from pulp_deb.plugins.importers.downloaders.exceptions import FileNotFoundException
from pulp_deb.plugins.importers.downloaders.local import LocalDownloader
from pulp_deb.plugins.importers.downloaders import url_utils


def resource_urls(config):
    return [r['resource'] for r in url_utils.get_resources(config)]


class LocalDownloaderTests(base_downloader.BaseDownloaderTests):

    def setUp(self):
        super(LocalDownloaderTests, self).setUp()
        self.config.repo_plugin_config.update(samples.valid_repo())
        self.downloader = LocalDownloader(self.repo, None, self.config, self.mock_cancelled_callback)

    def test_retrieve_resource(self):
        # Test
        resources = self.downloader.retrieve_resources(self.mock_progress_report)

        # Verify
        self.assertEqual(2, len(resources))

        repo = model.Repository()
        repo.update_from_resources(resources)
        self.assertEqual(2, len(repo.packages))

        self.assertEqual(2, self.mock_progress_report.query_total_count)
        self.assertEqual(2, self.mock_progress_report.query_finished_count)
        self.assertEqual(2, self.mock_progress_report.update_progress.call_count)

    def test_retrieve_metadata_no_metadata_found(self):
        # Setup
        self.config.repo_plugin_config.pop('dist')

        # Test & Verify
        try:
            self.downloader.retrieve_resources(self.mock_progress_report)
            self.fail()
        except FileNotFoundException, e:
            self.assertEqual(e.location in resource_urls(self.config), True)

    def test_retrieve_deb(self):
        # Test
        deb_path = self.downloader.retrieve_deb(self.mock_progress_report, self.deb)

        # Verify
        expected = os.path.join(samples.valid_repo()['url'], self.deb.filename())
        self.assertEqual(expected[len('file://'):], deb_path)

    def test_retrieve_deb_no_file(self):
        # Setup
        def _x():
            return 'not existant'
        self.deb.filename = _x

        # Test
        try:
            self.downloader.retrieve_deb(self.mock_progress_report, self.deb)
            self.fail()
        except FileNotFoundException, e:
            expected = os.path.join(samples.valid_repo()['url'][len('file://'):], self.deb.filename())
            self.assertEqual(expected, e.location)
