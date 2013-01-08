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

"""
Determines the correct downloader implementation to return based on the
url type.
"""

import logging
from stevedore import driver

from pulp_deb.plugins.importers.downloaders.exceptions import UnsupportedURLType, InvalidURL
from pulp_deb.plugins.importers.downloaders import url_utils


# -- constants ----------------------------------------------------------------

NAMESPACE = 'pulp.downloaders.deb'

LOG = logging.getLogger(__name__)


# -- public -------------------------------------------------------------------

def get_downloader(url, repo, conduit, config, is_cancelled_call):
    """
    Returns an instance of the correct downloader to use for the given url.

    :param url: location from which to sync packages
    :type  url: str

    :param repo: describes the repository being synchronized
    :type  repo: pulp.plugins.model.Repository

    :param conduit: sync conduit used during the sync process
    :type  conduit: pulp.plugins.conduits.repo_sync.RepoSyncConduit

    :param config: configuration of the importer and call
    :type  config: pulp.plugins.config.PluginCallConfiguration

    :param is_cancelled_call: callback into the plugin to check if the sync
           has been cancelled
    :type  is_cancelled_call: func

    :return: downloader instance to use for the given url

    :raise UnsupportedURLType: if there is no applicable downloader for the
           given url
    :raise InvalidURL: if the url cannot be parsed to determine the type
    """
    url_type = url_utils.determine_url_type(url)
    downloader = get_url_type_downloader(url_type)
    return downloader(repo, conduit, config, is_cancelled_call)


def is_valid_url(url):
    if not url or url is None:
        return False

    url_type = url_utils.determine_url_type(url)
    try:
        get_url_type_downloader(url_type)
        return True
    except UnsupportedURLType:
        return False


def get_url_type_downloader(url_type):
    """
    Gets the downloader class from url_type using stevedore
    """
    try:
        mgr = driver.DriverManager(NAMESPACE, url_type)
    except RuntimeError:
        # FIXME: Should look better...
        raise UnsupportedURLType(url_type)
    return mgr.driver
