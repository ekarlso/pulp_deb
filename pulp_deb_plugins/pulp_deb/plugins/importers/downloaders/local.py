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
import ipdb

from pulp_deb.plugins.importers.downloaders.base import BaseDownloader
from pulp_deb.plugins.importers.downloaders.exceptions import FileNotFoundException
from pulp_deb.plugins.importers.downloaders import url_utils
from pulp_deb.common import constants


def strip_scheme(url):
    return url[len('file://'):]


class LocalDownloader(BaseDownloader):
    """
    Used when the source for deb packages is a directory local to the Pulp
    server.
    """

    def retrieve_resources(self, progress_report):
        resources = url_utils.get_resources(self.config)
        #ipdb.set_trace()

        # Only do one query for this implementation
        progress_report.query_finished_count = 0
        progress_report.query_total_count = (len(resources))
        progress_report.update_progress()

        for resource in resources:
            progress_report.current_query = resource['resource']

            if not os.path.exists(strip_scheme(resource['resource'])):
                # The caller will take care of stuffing this error into the
                # progress report
                raise FileNotFoundException(resource['resource'])

            f = open(resource['resource'][len('file://'):], 'r')
            resource['contents'] = f.readlines()
            f.close()

            progress_report.query_finished_count += 1
        progress_report.update_progress()
        return resources

    def retrieve_deb(self, progress_report, deb):
        # Determine the full path to the existing deb on disk. This assumes
        # a structure where the deb are located in the same directory as
        # specified in the feed.
        repo = self.config.get(constants.CONFIG_URL)
        url = url_utils.get_deb_url(repo, deb)

        if not os.path.exists(url):
            raise FileNotFoundException(url)

        return url
