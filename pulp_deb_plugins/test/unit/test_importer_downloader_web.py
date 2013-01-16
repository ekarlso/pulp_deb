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
import pycurl
import shutil
import tempfile
import unittest

import mock

import base_downloader
from pulp_deb.common import samples
from pulp_deb.plugins.importers.downloaders import exceptions
from pulp_deb.plugins.importers.downloaders import web
from pulp_deb.plugins.importers.downloaders.web import HttpDownloader


URL = 'http://ubuntu.uib.no/archive'


class HttpDownloaderTests(base_downloader.BaseDownloaderTests):
    def setUp(self):
        super(HttpDownloaderTests, self).setUp()
        self.dist = samples.get_repo(url=URL)
        self.downloader = HttpDownloader(self.repo, None, self.config, self.mock_cancelled_callback)

    @mock.patch('pycurl.Curl')
    def test_download_resources(self, mock_curl_constructor):
        # Setup
        indexes = self.dist.get_indexes()

        mock_curl = mock.MagicMock()
        mock_curl.getinfo.return_value = 200 # simulate a successful download
        mock_curl_constructor.return_value = mock_curl

        # Test
        resources = self.downloader.download_resources(indexes, self.mock_progress_report)

        # Verify
        self.assertEqual(3, len(resources))

        self._ensure_path_exists(resources)

        # Progress indicators
        self.assertEqual(self.mock_progress_report.query_finished_count, 3)
        self.assertEqual(self.mock_progress_report.query_total_count, 3)
        self.assertEqual(self.mock_progress_report.update_progress.call_count, 4)

    @mock.patch('pycurl.Curl')
    def test_download_resources_404(self, mock_curl_constructor):
        # Setup
        indexes = self.dist.get_indexes()
        indexes[0]['url'] = indexes[0]['url'] + '_'

        mock_curl = mock.MagicMock()
        mock_curl.getinfo.return_value = 404 # simulate an error
        mock_curl_constructor.return_value = mock_curl

        # Test & Verify
        try:
            self.downloader.download_resources(indexes, self.mock_progress_report)
            self.fail()
        except exceptions.FileNotFoundException, e:
            self.assertEqual(indexes[0]['url'], e.location)
            self.assertEqual('path' in indexes[0], False)

    @mock.patch('pycurl.Curl')
    def test_download_packages(self, mock_curl_constructor):
        self.dist.add_package(self.dist.components[0]['name'], self.pkg)

        # Setup
        mock_curl = mock.MagicMock()
        mock_curl.getinfo.return_value = 200 # simulate a successful download
        mock_curl_constructor.return_value = mock_curl

        pkg_resources = self.dist.get_package_resources()

        # Test
        self.downloader.download_resources(pkg_resources, self.mock_progress_report)

        # Verify
        self._ensure_path_exists(pkg_resources)

    @mock.patch('pycurl.Curl')
    def test_download_packages_404(self, mock_curl_constructor):
        self.dist.add_package(self.dist.components[0]['name'], self.pkg)

        # Setup
        mock_curl = mock.MagicMock()
        mock_curl.getinfo.return_value = 404 # simulate a not found
        mock_curl_constructor.return_value = mock_curl

        pkg_resources = self.dist.get_package_resources()
        pkg_resources[0]['url'] = pkg_resources[0]['url'] + '_'

        # Test & Verify
        try:
            self.downloader.download_resources(pkg_resources, self.mock_progress_report)
            self.fail()
        except exceptions.FileNotFoundException, e:
            self.assertTrue(pkg_resources[0]['url'] in e.location)
            self.assertTrue('destination' not in pkg_resources[0])

    @mock.patch('pulp_deb.plugins.importers.downloaders.web.HttpDownloader._create_and_configure_curl')
    def test_download_file(self, mock_curl_create):
        mock_curl = mock.MagicMock()
        mock_curl.getinfo.return_value = 200
        mock_curl_create.return_value = mock_curl

        url = 'http://localhost/package.tar.gz'
        destination = mock.MagicMock()

        # Test
        self.downloader._download_file(url, destination)

        # Verify
        opts_by_key = curl_opts_by_key(mock_curl.setopt.call_args_list)
        self.assertEqual(opts_by_key[pycurl.URL], url)
        self.assertEqual(opts_by_key[pycurl.WRITEFUNCTION], destination.update)

        self.assertEqual(1, mock_curl.perform.call_count)
        self.assertEqual(1, mock_curl.getinfo.call_count)
        self.assertEqual(1, mock_curl.close.call_count)

    @mock.patch('pulp_deb.plugins.importers.downloaders.web.HttpDownloader._create_and_configure_curl')
    def test_download_file_unauthorized(self, mock_curl_create):
        # Setup
        mock_curl = mock.MagicMock()
        mock_curl.getinfo.return_value = 401
        mock_curl_create.return_value = mock_curl

        url = 'http://localhost/package.tar.gz'
        destination = mock.MagicMock()

        # Test
        try:
            self.downloader._download_file(url, destination)
            self.fail()
        except exceptions.UnauthorizedException, e:
            self.assertEqual(e.location, url)

    @mock.patch('pulp_deb.plugins.importers.downloaders.web.HttpDownloader._create_and_configure_curl')
    def test_download_file_not_found(self, mock_curl_create):
        # Setup
        mock_curl = mock.MagicMock()
        mock_curl.getinfo.return_value = 404
        mock_curl_create.return_value = mock_curl

        url = 'http://localhost/package.tar.gz'
        destination = mock.MagicMock()

        # Test
        try:
            self.downloader._download_file(url, destination)
            self.fail()
        except exceptions.FileNotFoundException, e:
            self.assertEqual(e.location, url)

    @mock.patch('pulp_deb.plugins.importers.downloaders.web.HttpDownloader._create_and_configure_curl')
    def test_download_file_unhandled_error(self, mock_curl_create):
        # Setup
        mock_curl = mock.MagicMock()
        mock_curl.getinfo.return_value = 500
        mock_curl_create.return_value = mock_curl

        url = 'http://localhost/package.tar.gz'
        destination = mock.MagicMock()

        # Test
        try:
            self.downloader._download_file(url, destination)
            self.fail()
        except exceptions.FileRetrievalException, e:
            self.assertEqual(e.location, url)

    @mock.patch('pycurl.Curl')
    def test_create_and_configure_curl(self, mock_constructor):
        # PyCurl doesn't give visibility into what options are set, so mock out
        # the constructor so we can check what's being set on the curl instance

        # Test
        mock_constructor.return_value = mock.MagicMock()
        curl = self.downloader._create_and_configure_curl()

        # Verify
        opts_by_key = curl_opts_by_key(curl.setopt.call_args_list)

        self.assertEqual(opts_by_key[pycurl.VERBOSE], 0)
        self.assertEqual(opts_by_key[pycurl.LOW_SPEED_LIMIT], 1000)
        self.assertEqual(opts_by_key[pycurl.LOW_SPEED_TIME], 5 * 60)

    def test_create_download_tmp_dir(self):
        # Test
        created = web._create_download_tmp_dir(self.working_dir)

        # Verify
        self.assertTrue(os.path.exists(created))
        self.assertEqual(created, os.path.join(self.working_dir, web.DOWNLOAD_TMP_DIR))


class InMemoryDownloadedContentTests(unittest.TestCase):
    def test_update(self):
        # Setup
        data = ['abc', 'de', 'fgh']

        # Test
        content = web.InMemoryDownloadedContent()
        for d in data:
            content.update(d)

        # Verify
        self.assertEqual(content.content, ''.join(data))


class StoredDownloadedContentTests(unittest.TestCase):

    def test_update(self):
        # Setup
        tmp_dir = tempfile.mkdtemp(prefix='stored-downloaded-content')
        filename = os.path.join(tmp_dir, 'storage-test.txt')
        data = ['abc', 'de', 'fgh']

        # Test - Store
        content = web.StoredDownloadedContent(filename)
        content.open()
        for d in data:
            content.update(d)
        content.close()

        # Verify
        self.assertTrue(os.path.exists(filename))
        f = open(filename, 'r')
        stored = f.read()
        f.close()
        self.assertEqual(stored, ''.join(data))

        # Test - Delete
        content.delete()

        # Verify
        self.assertTrue(not os.path.exists(filename))

        # Clean Up
        shutil.rmtree(tmp_dir)


def curl_opts_by_key(call_args_list):
    opts_by_key = dict([(c[0][0], c[0][1]) for c in call_args_list])
    return opts_by_key
