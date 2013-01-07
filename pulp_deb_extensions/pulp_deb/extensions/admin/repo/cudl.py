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
        notes[constants.REPO_NOTE_KEY] = constants.REPO_NOTE

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
            constants.CONFIG_SERVE_INSECURE: kwargs[OPTION_INSECURE.keyword],
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
        self.context.prompt.render_success_message(msg % {'r': repo_id})


class UpdateRepositoryCommand(cudl.UpdateRepositoryCommand):
    def run(self, **kwargs):
        # -- repository metadata --
        repo_id = kwargs.pop(options.OPTION_REPO_ID.keyword)
        description = kwargs.pop(options.OPTION_DESCRIPTION.keyword, None)
        name = kwargs.pop(options.OPTION_NAME.keyword, None)
        notes = kwargs.pop(options.OPTION_NOTES.keyword, None)

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
            constants.CONFIG_SERVE_INSECURE: kwargs[OPTION_INSECURE.keyword],
        }

        arg_utils.convert_removed_options(distributor_config)
        arg_utils.convert_boolean_arguments((constants.CONFIG_SERVE_HTTP, constants.CONFIG_SERVE_HTTPS), distributor_config)

        distributor_configs = {constants.DISTRIBUTOR_ID: distributor_config}

        # -- server update --
        response = self.context.server.repo.update_repo_and_plugins(repo_id, name,
            description, notes, importer_config, distributor_configs)

        if not response.is_async():
            msg = _('Repository [%(r)s] successfully updated')
            self.context.prompt.render_success_message(msg % {'r': repo_id})
        else:
            d = _('Repository update postponed due to another operation. Progress '
                  'on this task can be viewed using the commands under "repo tasks".')
            self.context.prompt.render_paragraph(d, tag='postponed')
            self.context.prompt.render_reasons(response.response_body.reasons)


class ListRepositoriesCommand(cudl.ListRepositoriesCommand):
    def __init__(self, context):
        repos_title = _('Deb Repositories')
        super(ListRepositoriesCommand, self).__init__(context,
                                                            repos_title=repos_title)

        # Both get_repositories and get_other_repositories will act on the full
        # list of repositories. Lazy cache the data here since both will be
        # called in succession, saving the round trip to the server.
        self.all_repos_cache = None

    def get_repositories(self, query_params, **kwargs):
        all_repos = self._all_repos(query_params, **kwargs)

        repos = []
        for repo in all_repos:
            notes = repo['notes']
            if constants.REPO_NOTE_KEY in notes and notes[constants.REPO_NOTE_KEY] == constants.REPO_NOTE:
                repos.append(repo)

        for repo in repos:
            if repo.get('distributors'):
                repo['distributors'][0]['relative_path'] = 'deb/%s/' % repo['id']

        return repos

    def get_other_repositories(self, query_params, **kwargs):
        all_repos = self._all_repos(query_params, **kwargs)

        non_repos = []
        for repo in all_repos:
            notes = repo['notes']
            if notes.get(constants.REPO_NOTE_KEY, None) != constants.REPO_NOTE:
                non_repos.append(repo)

        return non_repos

    def _all_repos(self, query_params, **kwargs):
        # This is safe from any issues with concurrency due to how the CLI works
        if self.all_repos_cache is None:
            self.all_repos_cache = self.context.server.repo.repositories(query_params).response_body

        return self.all_repos_cache


class SearchRepositoriesCommand(CriteriaCommand):
    def __init__(self, context):
        super(SearchRepositoriesCommand, self).__init__(
            self.run, name='search', description=DESC_SEARCH,
            include_search=True)

        self.context = context
        self.prompt = context.prompt

    def run(self, **kwargs):
        self.prompt.render_title(_('Repositories'))

        # Limit to only repositories
        if kwargs.get('str-eq', None) is None:
            kwargs['str-eq'] = []
        kwargs['str-eq'].append(['notes.%s' % constants.REPO_NOTE_KEY, constants.REPO_NOTE])

        # Server call
        repo_list = self.context.server.repo_search.search(**kwargs)

        # Display the results
        order = ['id', 'display_name', 'description']
        self.prompt.render_document_list(repo_list, order=order)
