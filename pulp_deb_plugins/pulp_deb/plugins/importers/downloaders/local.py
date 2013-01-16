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

from pulp_deb.common import utils
from pulp_deb.plugins.importers.downloaders.base import BaseDownloader
from pulp_deb.plugins.importers.downloaders.exceptions import FileNotFoundException


class LocalDownloader(BaseDownloader):
    """
    Used when the source for deb packages is a directory local to the Pulp
    server.
    """

    def download_resources(self, resources, progress_report, in_memory=False):
        # Only do one query for this implementation
        progress_report.query_finished_count = 0
        progress_report.query_total_count = (len(resources))
        progress_report.update_progress()

        for resource in resources:
            progress_report.current_query = resource['url']
            path = resource['url'][len('file://'):]

            if not os.path.exists(path):
                # The caller will take care of stuffing this error into the
                # progress report
                raise FileNotFoundException(resource['url'])

            if in_memory:
                resource['content'] = utils._read(path, as_list=True)
            else:
                resource['path'] = resource['url'][len('file://'):]

            progress_report.query_finished_count += 1
        progress_report.update_progress()
        return resources
