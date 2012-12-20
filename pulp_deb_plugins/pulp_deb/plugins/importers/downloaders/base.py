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


class BaseDownloader(object):
    """
    Base class all downloaders should extend. The factory will pass the
    necessary data to the constructor; any subclass should support the
    same signature to ensure the factory can create it.
    """

    def __init__(self, repo, conduit, config, is_cancelled_call):
        self.repo = repo
        self.conduit = conduit
        self.config = config
        self.is_cancelled_call = is_cancelled_call

    def retrieve_resources(self, progress_report):
        """
        Retrieve all Package, Source and Content lists for the given Repo

        :param progress_report: used to communicate the progress of this operation
        :type  progress_report: pulp_deb.importer.sync_progress.ProgressReport

        :return: list Resource (Packages, Sources.... .gz) documents describing all deb to import
        :rtype:  list
        """
        raise NotImplementedError()

    def retrieve_deb(self, progress_report, deb):
        """
        Retrieve a .deb file based on the deb object

        :param progress_report: used if any updates need to be made as the
               download runs
        :type  progress_report: pulp_deb.importer.sync_progress.ProgressReport

        :param deb: deb to download
        :type  deb: pulp_deb.common.model.DebianPackage

        :return: full path to the temporary location where the deb file is
        :rtype:  str
        """
        raise NotImplementedError()
