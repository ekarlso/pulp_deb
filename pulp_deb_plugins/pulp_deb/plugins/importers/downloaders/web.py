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

import copy
import logging
import os

import pycurl
from pulp.common.util import encode_unicode

from pulp_deb.common import constants
from pulp_deb.plugins.importers.downloaders import base, exceptions, url_utils


# -- constants ----------------------------------------------------------------


DOWNLOAD_TMP_DIR = 'http-downloads'

_LOG = logging.getLogger(__name__)


# -- downloader implementations -----------------------------------------------


class HttpDownloader(base.BaseDownloader):
    """
    Used when the source for deb packages is a remote source over HTTP.
    """

    def download_resources(self, resources, progress_report, in_memory=False):
        """
        Retrieves all metadata documents needed to fulfill the configuration
        set for the repository. The progress report will be updated as the
        downloads take place.

        :param progress_report: used to communicate the progress of this operation
        :type  progress_report: pulp_deb.importer.sync_progress.ProgressReport

        :return: Resources needed to download packages
        :rtype:  list
        """
        # Update the progress report to reflect the number of queries it will take
        progress_report.query_finished_count = 0
        progress_report.query_total_count = len(resources)

        for resource in resources:
            _LOG.info('Retrieving URL <%s>' % resource['url'])
            progress_report.current_query = resource['url']
            progress_report.update_progress()

            # Let any exceptions from this bubble up, the caller will update
            # the progress report as necessary
            if in_memory:
                content = InMemoryDownloadedContent()
                self._download_file(resource['url'], content)
                resource['content'] = content.content
            else:
                tmp_dir = _create_download_tmp_dir(self.repo.working_dir)

                name = resource.get('path', resource['source'].split('/')[-1])
                tmp_filename = os.path.join(tmp_dir, name)

                content = StoredDownloadedContent(tmp_filename)
                content.open()
                try:
                    self._download_file(resource['url'], content)
                    content.close()
                except:
                    content.close()
                    content.delete()
                    raise
                resource['path'] = tmp_filename

            progress_report.query_finished_count += 1

        progress_report.update_progress() # to get the final finished count out there
        return resources

    def _download_file(self, url, destination):
        """
        Downloads the content at the given URL into the given destination.
        The object passed into destination must have a method called "update"
        that accepts a single parameter (the buffer that was read).

        :param url: location to download
        :type  url: str

        :param destination: object
        @return:
        """
        curl = self._create_and_configure_curl()

        url = encode_unicode(url) # because of how the config is stored in pulp

        curl.setopt(pycurl.URL, url)
        curl.setopt(pycurl.WRITEFUNCTION, destination.update)
        curl.perform()
        status = curl.getinfo(curl.HTTP_CODE)
        curl.close()

        if status == 401:
            raise exceptions.UnauthorizedException(url)
        elif status == 404:
            raise exceptions.FileNotFoundException(url)
        elif status != 200:
            raise exceptions.FileRetrievalException(url)

    def _create_and_configure_curl(self):
        """
        Instantiates and configures the curl instance. This will drive the
        bulk of the behavior of how the download progresses. The values in
        this call should be tweaked or pulled out as repository-level
        configuration as the download process is enhanced.

        :return: curl instance to use for the download
        :rtype:  pycurl.Curl
        """

        curl = pycurl.Curl()

        # Eventually, add here support for:
        # - callback on bytes downloaded
        # - bandwidth limitations
        # - SSL verification for hosts on SSL
        # - client SSL certificate
        # - proxy support
        # - callback support for resuming partial downloads

        curl.setopt(pycurl.VERBOSE, 0)

        # TODO: Add in reference to is cancelled hook to be able to abort the download

        # Close out the connection on our end in the event the remote host
        # stops responding. This is interpretted as "If less than 1000 bytes are
        # sent in a 5 minute interval, abort the connection."
        curl.setopt(pycurl.LOW_SPEED_LIMIT, 1000)
        curl.setopt(pycurl.LOW_SPEED_TIME, 5 * 60)
        return curl


# -- private classes ----------------------------------------------------------


class InMemoryDownloadedContent(object):
    """
    In memory storage that content will be written to by PyCurl.
    """
    def __init__(self):
        self.content = ''

    def update(self, buffer):
        self.content += buffer


class StoredDownloadedContent(object):
    """
    Stores content on disk as it is retrieved by PyCurl. This currently does
    not support resuming a download and will need to be revisited to add
    that support.
    """
    def __init__(self, filename):
        self.filename = filename

        self.offset = 0
        self.file = None

    def open(self):
        """
        Sets the content object to be able to accept and store data sent to
        its update method.
        """
        self.file = open(self.filename, 'a+')

    def update(self, buffer):
        """
        Callback passed to PyCurl to use to write content as it is read.
        """
        self.file.seek(self.offset)
        self.file.write(buffer)
        self.offset += len(buffer)

    def close(self):
        """
        Closes the underlying file backing this content unit.
        """
        self.file.close()

    def delete(self):
        """
        Deletes the stored file.
        """
        if os.path.exists(self.filename):
            os.remove(self.filename)


# -- utilities ----------------------------------------------------------------


def _create_download_tmp_dir(repo_working_dir):
    tmp_dir = os.path.join(repo_working_dir, DOWNLOAD_TMP_DIR)
    if not os.path.exists(tmp_dir):
        os.mkdir(tmp_dir)
    return tmp_dir

