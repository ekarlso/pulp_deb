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


from gettext import gettext as _

from pulp_deb.common import constants
from pulp_deb.plugins.importers.downloaders import factory
from pulp_deb.plugins.importers.downloaders import url_utils


def validate(config):
    """
    Validates the configuration for the package package importer.

    :param config: configuration passed in by Pulp
    :type  config: pulp.plugins.config.PluginCallConfiguration

    :return: the expected return from the plugin's validate_config method
    :rtype:  tuple
    """

    validations = (
        _validate_resources,
        _validate_remove_missing,
        _validate_queries,
    )

    for validator in validations:
        result, msg = validator(config)
        if not result:
            return result, msg

    return True, None


def _validate_resources(config):
    """
    Validates the location of the repo
    """
    repo = url_utils.get_repo(config)

    if not repo.get(constants.CONFIG_URL, None):
        return True, None

    if not factory.is_valid_url(repo['url']):
        msg = 'URL for repo %(url)s is errorous'
        return False, _(msg) % repo

    try:
        url_utils.get_resources(config)
    except (KeyError, TypeError):
        msg = 'Resources error for %(url)s %(dist)s %(component)s %(architecture)s'
        return False, _(msg) % repo
    return True, None


def _validate_queries(config):
    """
    Validates the query parameters to apply to the source repo.
    """

    # The queries are optional
    if constants.CONFIG_QUERIES not in config.keys():
        return True, None

    queries = config.get(constants.CONFIG_QUERIES)
    if not isinstance(queries, (list, tuple)):
        msg = 'The value for <%(q)s> must be specified as a list'
        return False, _(msg) % {'q': constants.CONFIG_QUERIES}

    return True, None


def _validate_remove_missing(config):
    """
    Validates the remove missing packages value if it is specified.
    """

    # The flag is optional
    if constants.CONFIG_REMOVE_MISSING not in config.keys():
        return True, None

    # Make sure it's a boolean
    parsed = config.get_boolean(constants.CONFIG_REMOVE_MISSING)
    if parsed is None:
        msg = 'The value for <%(r)s> must be either "true" or "false"'
        return False, _(msg) % {'r': constants.CONFIG_REMOVE_MISSING}
    return True, None
