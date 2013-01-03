# Copyright (C) 2012 Red Hat, Inc.
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

from pulp.client import arg_utils
from pulp.client.commands import options
from pulp.client.extensions.extensions import PulpCliOption
from pulp.client.commands.criteria import CriteriaCommand
from pulp.client.commands.repo import cudl

from pulp_deb.common import constants


DESC_URL = _('Base URL containing directories dists / pool and so on')
OPTION_URL = PulpCliOption('--url', DESC_URL, required=False)

DESC_DIST = _('Dist name to get, like "squeeze" or "precise"')
OPTION_DIST = PulpCliOption('--dist', DESC_DIST, required=False)

DESC_COMPONENT = _('Components to get like "main" or "non-free"')
OPTION_COMPONENT = PulpCliOption('--components', DESC_COMPONENT, required=False)

DESC_ARCH = _('Archs to get like "amd64" or "noarch"')
OPTION_ARCH = PulpCliOption('--arch', DESC_ARCH, required=False)


DESC_QUERY = _(
    'query to issue against the feed\'s modules.json file to scope which '
    'modules are imported; multiple queries may be added by specifying this '
    'argument multiple times'
)
OPTION_QUERY = PulpCliOption('--query', DESC_QUERY, required=False, allow_multiple=True)

DESC_INSECURE = _('if "true", the repository will be served over HTTPS; defaults to false')
OPTION_INSECURE = PulpCliOption('--serve-insecure', DESC_INSECURE, required=False)

DESC_SEARCH = _('searches for Deb repositories on the server')


class CreateRepositoryCommand(cudl.CreateRepositoryCommand):
    def __init__(self, context):
        super(CreateRepositoryCommand, self).__init__(context)

        self.add_option(OPTION_URL)
        self.add_option(OPTION_DIST)
        self.add_option(OPTION_COMPONENT)
        self.add_option(OPTION_ARCH)
        self.add_option(OPTION_QUERY)
        self.add_option(OPTION_INSECURE)

    def run(self, **kwargs):
        repo_id = kwargs[options.OPTION_REPO_ID.keyword]
        description = kwargs[options.OPTION_DESCRIPTION.keyword]
        notes = kwargs.pop(options.OPTION_NOTES.keyword) or {}

        # Add a note to indicate this is a Deb repository
        notes[constants.REPO_NOTE_KEY] = constants.REPO_NOTE_DEB

        name = repo_id
        if options.OPTION_NAME.keyword in kwargs:
            name = kwargs[options.OPTION_NAME.keyword]

        # -- importer metadata --
        importer_config = {
            constants.CONFIG_URL: kwargs[OPTION_URL.keyword],
            constants.CONFIG_DIST: kwargs[OPTION_DIST.keyword],
            constants.CONFIG_COMPONENT: kwargs[OPTION_COMPONENT.keyword],
            constants.CONFIG_ARCH: kwargs[OPTION_ARCH.keyword],
            constants.CONFIG_QUERIES: kwargs[OPTION_QUERY.keyword],
        }
        arg_utils.convert_removed_options(importer_config)

        # -- distributor metadata --
        distributor_config = {
            constants.CONFIG_SERVE_INSECURE : kwargs[OPTION_INSECURE.keyword],
        }

        arg_utils.convert_removed_options(distributor_config)
        arg_utils.convert_boolean_arguments((constants.CONFIG_SERVE_INSECURE), distributor_config)

        distributors = [
            dict(distributor_type=constants.DISTRIBUTOR_TYPE_ID, distributor_config=distributor_config,
                 auto_publish=True, distributor_id=constants.DISTRIBUTOR_ID)
        ]

        # Create the repository
        self.context.server.repo.create_and_configure(repo_id, name, description,
            notes, constants.IMPORTER_TYPE_ID, importer_config)
        #notes, constants.IMPORTER_TYPE_ID, importer_config, distributors)
        msg = _('Successfully created repository [%(r)s]')
        self.context.prompt.render_success_message(msg % {'r' : repo_id})


class UpdateRepositoryCommand(cudl.UpdateRepositoryCommand):
    pass


class ListRepositoriesCommand(cudl.ListRepositoriesCommand):
    pass


class SearchRepositoriesCommand(CriteriaCommand):
    pass
